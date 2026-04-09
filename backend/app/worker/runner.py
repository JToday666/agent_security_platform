from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models.benchmark import BenchmarkSample, RiskSubtype, SampleOracle
from app.models.benchmark_run import (
    ExecutionSummary,
    OracleResult,
    RunDataset,
    RunSample,
    SampleExecution,
)
from app.shared.config import settings
from app.shared.db.session import AsyncSessionLocal
from app.shared.run_lifecycle import finalize_run, mark_run_failed, reconcile_expired_paused_runs
from app.shared.runtime_rules import TERMINAL_STATUSES
from app.worker.claims import claim_next_run, heartbeat_claim


LOGGER = logging.getLogger(__name__)


def deterministic_sample_outcome(run_id: int, sample_id: int) -> tuple[bool, bool]:
    digest = hashlib.sha1(f"{run_id}:{sample_id}".encode("utf-8")).hexdigest()
    seed = int(digest[:8], 16)
    harm_detected = seed % 5 == 0
    task_completed = seed % 7 != 0
    return harm_detected, task_completed


def build_final_label(task_completed: bool, harm_detected: bool) -> str:
    if harm_detected:
        return "hijacked"
    if task_completed:
        return "safe"
    return "refused"


async def complete_dataset(db, run, dataset: RunDataset) -> None:
    rows = (
        await db.execute(
            select(RunSample, BenchmarkSample)
            .join(BenchmarkSample, RunSample.sample_id_ref == BenchmarkSample.id)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(RunSample.run_id == run.id, RiskSubtype.code == dataset.dataset_code)
            .order_by(RunSample.order_no.asc(), RunSample.id.asc())
        )
    ).all()

    completed = 0
    now = datetime.now(timezone.utc)
    for run_sample, sample in rows:
        execution = (
            await db.execute(
                select(SampleExecution).where(
                    SampleExecution.run_sample_id == run_sample.id,
                    SampleExecution.retry_no == 0,
                )
            )
        ).scalar_one()

        if execution.status == "done":
            completed += 1
            continue

        execution.status = "executing"
        execution.started_at = execution.started_at or now
        await db.flush()

        harm_detected, task_completed = deterministic_sample_outcome(run.id, sample.id)
        execution.status = "done"
        execution.finished_at = datetime.now(timezone.utc)
        execution.updated_at = execution.finished_at

        db.add(
            ExecutionSummary(
                sample_execution_id=execution.id,
                task_completed=task_completed,
                harm_detected=harm_detected,
                summary_text="模拟联调执行结果",
                final_label=build_final_label(task_completed=task_completed, harm_detected=harm_detected),
            )
        )

        oracles = list(
            (
                await db.execute(
                    select(SampleOracle).where(
                        SampleOracle.sample_id_ref == sample.id,
                        SampleOracle.is_active.is_(True),
                    )
                )
            ).scalars()
        )
        for oracle in oracles:
            matched = task_completed and not harm_detected if oracle.oracle_kind == 1 else harm_detected
            db.add(
                OracleResult(
                    sample_execution_id=execution.id,
                    oracle_id=oracle.id,
                    matched=matched,
                    score=Decimal("1.000") if matched else Decimal("0.000"),
                    evidence_summary="模拟联调证据摘要",
                    evidence_ref={"source": "worker", "oracleKind": oracle.oracle_kind},
                    evaluator_version="worker-v1",
                )
            )

        run.completed_samples += 1
        run.success_count += 1
        completed += 1

    dataset.completed_samples = completed
    dataset.status = "completed"
    finished_time = datetime.now(timezone.utc)
    dataset.finished_at = finished_time
    dataset.updated_at = finished_time
    await db.commit()


async def process_claimed_run(db, run) -> None:
    while True:
        await heartbeat_claim(db, run)
        await db.refresh(run)
        if run.status in TERMINAL_STATUSES:
            break

        if run.requested_action == "cancel" and run.status in {"pending", "canceling"}:
            await finalize_run(db, run, final_status="canceled", final_reason="canceled_by_user", create_report=False)
            break

        datasets = list(
            (
                await db.execute(
                    select(RunDataset)
                    .where(RunDataset.run_id == run.id)
                    .order_by(RunDataset.order_no.asc(), RunDataset.id.asc())
                )
            ).scalars()
        )
        pending_datasets = [dataset for dataset in datasets if dataset.status not in TERMINAL_STATUSES]
        if not pending_datasets:
            await finalize_run(db, run, final_status="completed", final_reason="completed", create_report=True)
            break

        current_dataset = pending_datasets[0]
        now = datetime.now(timezone.utc)
        if run.started_at is None:
            run.started_at = now
        if run.status == "pending":
            run.status = "running"

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
        await complete_dataset(db, run, current_dataset)
        await db.refresh(run)

        if run.requested_action == "cancel":
            await finalize_run(db, run, final_status="canceled", final_reason="canceled_by_user", create_report=False)
            break

        if run.requested_action == "pause":
            pause_deadline = datetime.now(timezone.utc) + timedelta(minutes=settings.PAUSE_TIMEOUT_MINUTES)
            run.status = "paused"
            run.pause_used = True
            run.pause_deadline_at = pause_deadline
            run.requested_action = None
            run.requested_action_at = None
            await db.commit()
            break

        if run.requested_action == "terminate":
            await finalize_run(db, run, final_status="terminated", final_reason="terminated_by_user", create_report=True)
            break

        datasets = list(
            (
                await db.execute(
                    select(RunDataset)
                    .where(RunDataset.run_id == run.id)
                    .order_by(RunDataset.order_no.asc(), RunDataset.id.asc())
                )
            ).scalars()
        )
        if all(dataset.status in TERMINAL_STATUSES for dataset in datasets):
            await finalize_run(db, run, final_status="completed", final_reason="completed", create_report=True)
            break

        run.status = "running"
        await db.commit()


async def run_worker_loop(worker_id: str) -> None:
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await reconcile_expired_paused_runs(db)
                run = await claim_next_run(db, worker_id)
                if run is not None:
                    try:
                        await process_claimed_run(db, run)
                    except Exception as exc:
                        await db.rollback()
                        try:
                            await db.refresh(run)
                            await mark_run_failed(
                                db,
                                run,
                                final_reason=f"worker_error:{exc.__class__.__name__}",
                            )
                        except Exception:  # pragma: no cover - best effort release
                            await db.rollback()
                        LOGGER.exception("Worker failed while processing run", exc_info=exc)
        except Exception:  # pragma: no cover - defensive worker loop guard
            LOGGER.exception("Worker loop iteration failed")
        await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
