"""Sample-level execution claim and heartbeat helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark_run import SampleExecution, TestRun
from app.platform.config import settings

SAMPLE_IN_FLIGHT_STATUSES = {"claimed", "dispatching", "executing", "verifying"}
SAMPLE_TERMINAL_STATUSES = {"done", "error", "canceled"}


def sample_claim_is_stale(
    lease_expires_at: datetime | None,
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether a sample execution lease has expired."""
    if lease_expires_at is None:
        return False
    current = now or datetime.now(timezone.utc)
    lease_deadline = lease_expires_at.astimezone(timezone.utc)
    return lease_deadline <= current


async def claim_next_sample(
    db: AsyncSession, worker_id: str
) -> SampleExecution | None:
    """Claim the next ready sample execution for one sample worker."""
    now = datetime.now(timezone.utc)
    lease_expires_at = now + timedelta(
        seconds=max(1, settings.SAMPLE_CLAIM_STALE_AFTER_SECONDS)
    )

    execution = (
        await db.execute(
            select(SampleExecution)
            .join(TestRun, SampleExecution.run_id == TestRun.id)
            .where(
                TestRun.status == "running",
                or_(
                    and_(
                        SampleExecution.status == "ready",
                        or_(
                            SampleExecution.ready_at.is_(None),
                            SampleExecution.ready_at <= now,
                        ),
                    ),
                    and_(
                        SampleExecution.status.in_(SAMPLE_IN_FLIGHT_STATUSES),
                        SampleExecution.lease_expires_at.is_not(None),
                        SampleExecution.lease_expires_at <= now,
                    ),
                )
            )
            .order_by(
                SampleExecution.ready_at.asc().nullsfirst(),
                SampleExecution.created_at.asc(),
                SampleExecution.id.asc(),
            )
            .limit(1)
            .with_for_update(skip_locked=True)
        )
    ).scalar_one_or_none()
    if execution is None:
        return None

    execution.status = "claimed"
    execution.claimed_by = worker_id
    execution.claimed_at = execution.claimed_at or now
    execution.claim_heartbeat_at = now
    execution.lease_expires_at = lease_expires_at
    execution.updated_at = now
    await db.commit()
    await db.refresh(execution)
    return execution


async def heartbeat_sample_claim_by_id(
    db: AsyncSession, execution_id: int, worker_id: str
) -> bool:
    """Refresh a sample execution lease when the claim is still owned by worker_id."""
    execution = await db.get(SampleExecution, execution_id)
    if (
        execution is None
        or execution.claimed_by != worker_id
        or execution.status not in SAMPLE_IN_FLIGHT_STATUSES
    ):
        return False
    now = datetime.now(timezone.utc)
    execution.claim_heartbeat_at = now
    execution.lease_expires_at = now + timedelta(
        seconds=max(1, settings.SAMPLE_CLAIM_STALE_AFTER_SECONDS)
    )
    execution.updated_at = now
    await db.commit()
    return True
