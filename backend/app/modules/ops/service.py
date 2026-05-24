"""Operational status aggregation for backend and workers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark_run import SampleExecution
from app.models.worker_process import WorkerProcess

SAMPLE_QUEUE_STATUSES = [
    "blocked",
    "ready",
    "claimed",
    "dispatching",
    "executing",
    "verifying",
    "done",
    "error",
    "canceled",
]


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


async def _sample_queue_counts(db: AsyncSession) -> dict[str, int]:
    rows = (
        await db.execute(
            select(SampleExecution.status, func.count())
            .group_by(SampleExecution.status)
        )
    ).all()
    counts = {status: 0 for status in SAMPLE_QUEUE_STATUSES}
    for status, count in rows:
        counts[str(status)] = int(count or 0)
    return counts


async def build_worker_status(
    db: AsyncSession, *, stale_after_seconds: int = 120
) -> dict[str, Any]:
    """Build lightweight worker and sample queue status for operators."""
    now = datetime.now(timezone.utc)
    stale_before = now - timedelta(seconds=stale_after_seconds)
    workers = list(
        (
            await db.execute(
                select(WorkerProcess).order_by(
                    WorkerProcess.role.asc(), WorkerProcess.worker_id.asc()
                )
            )
        ).scalars()
    )
    sample_queues = await _sample_queue_counts(db)

    alerts: list[dict[str, Any]] = []
    for worker in workers:
        if (
            worker.status == "healthy"
            and worker.last_heartbeat_at.astimezone(timezone.utc) < stale_before
        ):
            alerts.append(
                {
                    "type": "stale_worker",
                    "severity": "warning",
                    "workerId": worker.worker_id,
                    "role": worker.role,
                    "lastHeartbeatAt": _iso(worker.last_heartbeat_at),
                }
            )

    in_flight = (
        sample_queues["claimed"]
        + sample_queues["dispatching"]
        + sample_queues["executing"]
        + sample_queues["verifying"]
    )
    healthy_sample_workers = [
        worker
        for worker in workers
        if worker.role == "sample_worker"
        and worker.status == "healthy"
        and worker.last_heartbeat_at.astimezone(timezone.utc) >= stale_before
    ]
    if not healthy_sample_workers and (sample_queues["ready"] > 0 or in_flight > 0):
        alerts.append(
            {
                "type": "sample_workers_unavailable",
                "severity": "critical",
                "ready": sample_queues["ready"],
                "inFlight": in_flight,
            }
        )

    return {
        "generatedAt": _iso(now),
        "workers": [
            {
                "workerId": worker.worker_id,
                "role": worker.role,
                "hostname": worker.hostname,
                "pid": worker.pid,
                "status": worker.status,
                "startedAt": _iso(worker.started_at),
                "lastHeartbeatAt": _iso(worker.last_heartbeat_at),
                "activeCount": worker.active_count,
                "metadata": worker.process_metadata,
            }
            for worker in workers
        ],
        "sampleQueues": sample_queues,
        "alerts": alerts,
    }
