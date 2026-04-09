"""Worker 已认领任务处理逻辑。"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.benchmark_run import RunDataset
from app.modules.evaluations import lifecycle
from app.modules.evaluations.state_rules import TERMINAL_STATUSES
from app.shared.config import settings
from app.worker.claims import heartbeat_claim
from app.worker.execution import execute_dataset


async def load_run_datasets(db, run_id: int) -> list[RunDataset]:
    """按执行顺序加载任务下的数据集快照。"""
    return list(
        (
            await db.execute(
                select(RunDataset)
                .where(RunDataset.run_id == run_id)
                .order_by(RunDataset.order_no.asc(), RunDataset.id.asc())
            )
        ).scalars()
    )


async def process_claimed_run(db, run) -> None:
    """处理当前 worker 已认领的评测任务。"""
    while True:
        await heartbeat_claim(db, run)
        await db.refresh(run)
        if run.status in TERMINAL_STATUSES:
            break

        if run.requested_action == "cancel" and run.status in {"pending", "canceling"}:
            await lifecycle.finalize_run(
                db,
                run,
                final_status="canceled",
                final_reason="canceled_by_user",
                create_report=False,
            )
            break

        datasets = await load_run_datasets(db, run.id)
        pending_datasets = [dataset for dataset in datasets if dataset.status not in TERMINAL_STATUSES]
        if not pending_datasets:
            await lifecycle.finalize_run(
                db,
                run,
                final_status="completed",
                final_reason="completed",
                create_report=True,
            )
            break

        current_dataset = pending_datasets[0]
        now = datetime.now(timezone.utc)
        lifecycle.mark_run_started(run, now)

        if current_dataset.total_samples == 0:
            current_dataset.status = "completed"
            current_dataset.started_at = current_dataset.started_at or now
            current_dataset.finished_at = now
            current_dataset.updated_at = now
            await db.commit()
            continue

        current_dataset.status = "running"
        current_dataset.started_at = current_dataset.started_at or now
        current_dataset.updated_at = now
        await db.commit()

        await asyncio.sleep(0.01)
        await execute_dataset(db, run, current_dataset)
        await db.refresh(run)

        if run.requested_action == "cancel":
            await lifecycle.finalize_run(
                db,
                run,
                final_status="canceled",
                final_reason="canceled_by_user",
                create_report=False,
            )
            break

        if run.requested_action == "pause":
            pause_deadline = datetime.now(timezone.utc) + timedelta(minutes=settings.PAUSE_TIMEOUT_MINUTES)
            lifecycle.pause_after_current_dataset(run, pause_deadline)
            await db.commit()
            break

        if run.requested_action == "terminate":
            await lifecycle.finalize_run(
                db,
                run,
                final_status="terminated",
                final_reason="terminated_by_user",
                create_report=True,
            )
            break

        datasets = await load_run_datasets(db, run.id)
        if all(dataset.status in TERMINAL_STATUSES for dataset in datasets):
            await lifecycle.finalize_run(
                db,
                run,
                final_status="completed",
                final_reason="completed",
                create_report=True,
            )
            break

        lifecycle.keep_running(run)
        await db.commit()
