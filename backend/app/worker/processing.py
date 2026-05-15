"""Worker 已认领任务处理逻辑。"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.benchmark_run import RunDataset, TestRun
from app.modules.evaluations import lifecycle
from app.modules.evaluations.state_rules import TERMINAL_STATUSES
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal
from app.worker.claims import heartbeat_claim_by_id
from app.worker.execution import execute_dataset

LOGGER = logging.getLogger(__name__)


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


def resolve_timeout_seconds(run: TestRun) -> int:
    """Derive runtime timeout from the saved execution config."""
    parameters = (
        run.execution_config.get("parameters")
        if isinstance(run.execution_config, dict)
        else {}
    )
    timeout_minutes = (
        parameters.get("timeoutMinutes") if isinstance(parameters, dict) else None
    )
    if isinstance(timeout_minutes, (int, float)) and timeout_minutes > 0:
        return max(1, int(timeout_minutes * 60))
    return settings.WORKER_EXECUTION_TIMEOUT_SECONDS


def resolve_dispatch_mode(run: TestRun) -> str:
    """Resolve the worker dispatch mode for this run."""
    dispatch = (
        run.execution_config.get("dispatch")
        if isinstance(run.execution_config, dict)
        else None
    )
    if isinstance(dispatch, dict):
        mode = str(dispatch.get("mode") or "").strip().lower()
        if mode:
            return mode
    return settings.WORKER_DISPATCH_MODE_DEFAULT


def resolve_dispatch_config(run: TestRun) -> dict[str, object]:
    """Build dispatch config passed to runtime adapters."""
    execution_config = (
        run.execution_config if isinstance(run.execution_config, dict) else {}
    )
    parameters = (
        execution_config.get("parameters")
        if isinstance(execution_config.get("parameters"), dict)
        else {}
    )
    config: dict[str, object] = {
        "evaluationId": run.public_id,
        "maxSteps": (
            parameters.get("maxSteps") if isinstance(parameters, dict) else None
        ),
    }
    frozen_agent_snapshot = execution_config.get("frozenAgentSnapshot")
    if isinstance(frozen_agent_snapshot, dict):
        config["frozenAgentSnapshot"] = frozen_agent_snapshot
    return config


async def _heartbeat_loop(
    run_id: int, worker_id: str, stop_event: asyncio.Event
) -> None:
    """Refresh the run claim heartbeat while the run task is active."""
    while not stop_event.is_set():
        try:
            async with AsyncSessionLocal() as db:
                claimed = await heartbeat_claim_by_id(db, run_id, worker_id)
            if not claimed:
                return
        except Exception:
            LOGGER.exception(
                "Failed to heartbeat claimed run", extra={"run_id": run_id}
            )

        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=settings.WORKER_HEARTBEAT_INTERVAL_SECONDS
            )
        except asyncio.TimeoutError:
            continue


async def process_claimed_run(run_id: int, worker_id: str) -> None:
    """处理当前 worker 已认领的评测任务。"""
    stop_event = asyncio.Event()
    heartbeat_task = asyncio.create_task(_heartbeat_loop(run_id, worker_id, stop_event))

    try:
        while True:
            async with AsyncSessionLocal() as db:
                run = await db.get(TestRun, run_id)
                if run is None:
                    return
                if run.status in TERMINAL_STATUSES:
                    return

                if run.requested_action == "cancel" and run.status in {
                    "pending",
                    "canceling",
                }:
                    await lifecycle.finalize_run(
                        db,
                        run,
                        final_status="canceled",
                        final_reason="canceled_by_user",
                        create_report=False,
                    )
                    return

                datasets = await load_run_datasets(db, run.id)
                pending_datasets = [
                    dataset
                    for dataset in datasets
                    if dataset.status not in TERMINAL_STATUSES
                ]
                if not pending_datasets:
                    await lifecycle.finalize_run(
                        db,
                        run,
                        final_status="completed",
                        final_reason="completed",
                        create_report=True,
                    )
                    return

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

                dataset_id = current_dataset.id
                dataset_code = current_dataset.dataset_code
                dispatch_mode = resolve_dispatch_mode(run)
                dispatch_config = resolve_dispatch_config(run)
                timeout_seconds = resolve_timeout_seconds(run)

            await execute_dataset(
                run_id,
                dataset_id,
                dataset_code,
                dispatch_mode=dispatch_mode,
                dispatch_config=dispatch_config,
                timeout_seconds=timeout_seconds,
            )

            async with AsyncSessionLocal() as db:
                run = await db.get(TestRun, run_id)
                if run is None:
                    return

                if run.requested_action == "cancel":
                    await lifecycle.finalize_run(
                        db,
                        run,
                        final_status="canceled",
                        final_reason="canceled_by_user",
                        create_report=False,
                    )
                    return

                if run.requested_action == "pause":
                    pause_deadline = datetime.now(timezone.utc) + timedelta(
                        minutes=settings.PAUSE_TIMEOUT_MINUTES
                    )
                    lifecycle.pause_after_current_dataset(run, pause_deadline)
                    await db.commit()
                    return

                if run.requested_action == "terminate":
                    await lifecycle.finalize_run(
                        db,
                        run,
                        final_status="terminated",
                        final_reason="terminated_by_user",
                        create_report=True,
                    )
                    return

                datasets = await load_run_datasets(db, run.id)
                if all(dataset.status in TERMINAL_STATUSES for dataset in datasets):
                    await lifecycle.finalize_run(
                        db,
                        run,
                        final_status="completed",
                        final_reason="completed",
                        create_report=True,
                    )
                    return

                lifecycle.keep_running(run)
                await db.commit()
    finally:
        stop_event.set()
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task
