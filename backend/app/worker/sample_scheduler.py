"""Sample-level scheduler and run finalizer."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import RunDataset, RunSample, SampleExecution, TestRun
from app.modules.evaluations.lifecycle import (
    finalize_run,
    mark_run_started,
    pause_after_current_dataset,
    reconcile_expired_paused_runs,
)
from app.modules.evaluations.state_rules import TERMINAL_STATUSES
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal
from app.worker.sample_claims import SAMPLE_IN_FLIGHT_STATUSES

LOGGER = logging.getLogger(__name__)

SCHEDULABLE_RUN_STATUSES = {"pending", "running", "pausing", "terminating", "canceling"}
SAMPLE_NOT_STARTED_STATUSES = {"blocked", "ready"}
SAMPLE_RELEASE_OCCUPANCY_STATUSES = SAMPLE_IN_FLIGHT_STATUSES | {"ready"}


async def _count_samples(
    db: AsyncSession, *, run_id: int | None = None, statuses: set[str] | None = None
) -> int:
    stmt = select(func.count()).select_from(SampleExecution)
    if run_id is not None:
        stmt = stmt.where(SampleExecution.run_id == run_id)
    if statuses is not None:
        stmt = stmt.where(SampleExecution.status.in_(statuses))
    return int((await db.execute(stmt)).scalar_one() or 0)


async def _count_in_flight_for_user(db: AsyncSession, user_id: int) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(SampleExecution)
                .join(TestRun, SampleExecution.run_id == TestRun.id)
                .where(
                    TestRun.user_id == user_id,
                    SampleExecution.status.in_(SAMPLE_RELEASE_OCCUPANCY_STATUSES),
                )
            )
        ).scalar_one()
        or 0
    )


async def _count_in_flight_for_agent(db: AsyncSession, agent_base_url: str) -> int:
    return int(
        (
            await db.execute(
                select(func.count())
                .select_from(SampleExecution)
                .join(TestRun, SampleExecution.run_id == TestRun.id)
                .where(
                    TestRun.agent_base_url == agent_base_url,
                    SampleExecution.status.in_(SAMPLE_RELEASE_OCCUPANCY_STATUSES),
                )
            )
        ).scalar_one()
        or 0
    )


async def _latest_execution_statuses(
    db: AsyncSession, *, run_id: int, dataset_code: str | None = None
) -> dict[int, str]:
    stmt = (
        select(
            SampleExecution.run_sample_id,
            SampleExecution.retry_no,
            SampleExecution.status,
        )
        .join(RunSample, SampleExecution.run_sample_id == RunSample.id)
        .where(SampleExecution.run_id == run_id)
        .order_by(
            SampleExecution.run_sample_id.asc(),
            SampleExecution.retry_no.asc(),
            SampleExecution.id.asc(),
        )
    )
    if dataset_code is not None:
        stmt = (
            stmt.join(
                BenchmarkSample, SampleExecution.sample_id_ref == BenchmarkSample.id
            )
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(RiskSubtype.code == dataset_code)
        )

    rows = (await db.execute(stmt)).all()
    latest: dict[int, tuple[int, str]] = {}
    for run_sample_id, retry_no, status in rows:
        current = latest.get(run_sample_id)
        if current is None or int(retry_no) >= current[0]:
            latest[int(run_sample_id)] = (int(retry_no), str(status))
    return {run_sample_id: status for run_sample_id, (_, status) in latest.items()}


def _logical_counts(statuses: dict[int, str]) -> tuple[int, int, int, int]:
    total = len(statuses)
    done = sum(1 for status in statuses.values() if status == "done")
    failed = sum(1 for status in statuses.values() if status in {"error", "canceled"})
    terminal = done + failed
    return total, terminal, done, failed


async def _sync_completed_datasets(
    db: AsyncSession, run: TestRun, now: datetime
) -> None:
    datasets = list(
        (
            await db.execute(
                select(RunDataset)
                .where(RunDataset.run_id == run.id)
                .order_by(RunDataset.order_no.asc(), RunDataset.id.asc())
            )
        ).scalars()
    )
    for dataset in datasets:
        total, terminal, _, _ = _logical_counts(
            await _latest_execution_statuses(
                db, run_id=run.id, dataset_code=dataset.dataset_code
            )
        )
        dataset.completed_samples = terminal
        if total > 0 and total == terminal and dataset.status not in TERMINAL_STATUSES:
            dataset.status = "completed"
            dataset.finished_at = dataset.finished_at or now
        if total == 0 and dataset.status not in TERMINAL_STATUSES:
            dataset.status = "completed"
            dataset.finished_at = dataset.finished_at or now
        dataset.updated_at = now


async def _current_dataset(db: AsyncSession, run_id: int) -> RunDataset | None:
    return (
        await db.execute(
            select(RunDataset)
            .where(
                RunDataset.run_id == run_id,
                RunDataset.status.not_in(
                    ["completed", "terminated", "canceled", "failed"]
                ),
            )
            .order_by(RunDataset.order_no.asc(), RunDataset.id.asc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def _release_capacity(db: AsyncSession, run: TestRun) -> int:
    global_in_flight = await _count_samples(
        db, statuses=SAMPLE_RELEASE_OCCUPANCY_STATUSES
    )
    run_in_flight = await _count_samples(
        db, run_id=run.id, statuses=SAMPLE_RELEASE_OCCUPANCY_STATUSES
    )
    user_in_flight = await _count_in_flight_for_user(db, run.user_id)
    agent_in_flight = await _count_in_flight_for_agent(db, run.agent_base_url)
    return max(
        0,
        min(
            max(1, settings.SCHEDULER_RELEASE_BATCH_SIZE),
            max(0, settings.GLOBAL_MAX_IN_FLIGHT_SAMPLES - global_in_flight),
            max(0, settings.RUN_MAX_IN_FLIGHT_SAMPLES - run_in_flight),
            max(0, settings.USER_MAX_IN_FLIGHT_SAMPLES - user_in_flight),
            max(0, settings.AGENT_MAX_IN_FLIGHT_SAMPLES - agent_in_flight),
        ),
    )


async def _release_dataset_samples(
    db: AsyncSession, run: TestRun, dataset: RunDataset, limit: int, now: datetime
) -> int:
    if limit <= 0:
        return 0

    rows = (
        await db.execute(
            select(SampleExecution)
            .join(RunSample, SampleExecution.run_sample_id == RunSample.id)
            .join(BenchmarkSample, SampleExecution.sample_id_ref == BenchmarkSample.id)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(
                SampleExecution.run_id == run.id,
                SampleExecution.status == "blocked",
                RiskSubtype.code == dataset.dataset_code,
            )
            .order_by(RunSample.order_no.asc(), SampleExecution.id.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
    ).scalars()
    executions = list(rows)
    for execution in executions:
        execution.status = "ready"
        execution.ready_at = now
        execution.updated_at = now
    return len(executions)


async def _cancel_not_started_samples(
    db: AsyncSession, run_id: int, now: datetime
) -> int:
    result = await db.execute(
        update(SampleExecution)
        .where(
            SampleExecution.run_id == run_id,
            SampleExecution.status.in_(SAMPLE_NOT_STARTED_STATUSES),
        )
        .values(status="canceled", finished_at=now, updated_at=now)
    )
    return int(result.rowcount or 0)


async def _recompute_run_counters(db: AsyncSession, run: TestRun, now: datetime) -> None:
    _, terminal_count, done_count, error_count = _logical_counts(
        await _latest_execution_statuses(db, run_id=run.id)
    )
    run.completed_samples = terminal_count
    run.success_count = done_count
    run.failed_count = error_count
    run.updated_at = now


async def release_ready_samples_once(db: AsyncSession) -> int:
    """Release blocked sample executions into the ready queue once."""
    now = datetime.now(timezone.utc)
    runs = list(
        (
            await db.execute(
                select(TestRun)
                .where(TestRun.status.in_(SCHEDULABLE_RUN_STATUSES))
                .order_by(TestRun.created_at.asc(), TestRun.id.asc())
                .limit(25)
                .with_for_update(skip_locked=True)
            )
        ).scalars()
    )
    released_total = 0

    for run in runs:
        await _sync_completed_datasets(db, run, now)

        if run.status == "canceling" or run.requested_action == "cancel":
            await _cancel_not_started_samples(db, run.id, now)
            await _recompute_run_counters(db, run, now)
            await db.commit()
            continue

        if run.status == "terminating" or run.requested_action == "terminate":
            await _cancel_not_started_samples(db, run.id, now)
            await _recompute_run_counters(db, run, now)
            await db.commit()
            continue

        if run.status == "pausing" or run.requested_action == "pause":
            in_flight = await _count_samples(
                db, run_id=run.id, statuses=SAMPLE_IN_FLIGHT_STATUSES
            )
            if in_flight == 0:
                pause_after_current_dataset(
                    run, now + timedelta(minutes=settings.PAUSE_TIMEOUT_MINUTES)
                )
            await db.commit()
            continue

        mark_run_started(run, now)
        dataset = await _current_dataset(db, run.id)
        if dataset is None:
            await _recompute_run_counters(db, run, now)
            await db.commit()
            continue

        if dataset.status == "pending":
            dataset.status = "running"
            dataset.started_at = dataset.started_at or now
        dataset.updated_at = now

        capacity = await _release_capacity(db, run)
        released = await _release_dataset_samples(db, run, dataset, capacity, now)
        released_total += released
        await db.commit()

    return released_total


async def finalize_ready_runs_once(db: AsyncSession) -> int:
    """Finalize non-terminal runs whose sample executions have all reached terminal state."""
    now = datetime.now(timezone.utc)
    runs = list(
        (
            await db.execute(
                select(TestRun)
                .where(TestRun.status.not_in(list(TERMINAL_STATUSES | {"paused"})))
                .order_by(TestRun.created_at.asc(), TestRun.id.asc())
                .limit(25)
                .with_for_update(skip_locked=True)
            )
        ).scalars()
    )
    finalized = 0

    for run in runs:
        total, terminal, _, _ = _logical_counts(
            await _latest_execution_statuses(db, run_id=run.id)
        )
        if total == 0 or total != terminal:
            continue

        await _sync_completed_datasets(db, run, now)
        await _recompute_run_counters(db, run, now)

        if run.status == "canceling" or run.requested_action == "cancel":
            await finalize_run(
                db,
                run,
                final_status="canceled",
                final_reason="canceled_by_user",
                create_report=False,
            )
        elif run.status == "terminating" or run.requested_action == "terminate":
            await finalize_run(
                db,
                run,
                final_status="terminated",
                final_reason="terminated_by_user",
                create_report=True,
            )
        else:
            await finalize_run(
                db,
                run,
                final_status="completed",
                final_reason="all_samples_terminal",
                create_report=True,
            )
        finalized += 1

    return finalized


async def run_scheduler_loop() -> None:
    """Run scheduler and finalizer loops in one lightweight coordinator process."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await reconcile_expired_paused_runs(db)
                await release_ready_samples_once(db)
                await finalize_ready_runs_once(db)
        except Exception:
            LOGGER.exception("Sample scheduler loop iteration failed")
        await asyncio.sleep(settings.SCHEDULER_POLL_INTERVAL_SECONDS)
