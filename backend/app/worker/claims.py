from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark_run import TestRun
from app.shared.config import settings


def claim_is_stale(
    claim_heartbeat_at: datetime | None,
    stale_after_seconds: int | None = None,
    *,
    now: datetime | None = None,
) -> bool:
    if claim_heartbeat_at is None:
        return False
    current = now or datetime.now(timezone.utc)
    heartbeat = claim_heartbeat_at.astimezone(timezone.utc)
    timeout_seconds = stale_after_seconds or settings.RUN_CLAIM_STALE_AFTER_SECONDS
    return (current - heartbeat).total_seconds() > timeout_seconds


async def claim_next_run(db: AsyncSession, worker_id: str) -> TestRun | None:
    now = datetime.now(timezone.utc)
    stale_before = now - timedelta(seconds=settings.RUN_CLAIM_STALE_AFTER_SECONDS)
    run = (
        await db.execute(
            select(TestRun)
            .where(
                TestRun.status.in_(["pending", "running", "pausing", "terminating", "canceling"]),
                or_(
                    TestRun.claimed_by.is_(None),
                    TestRun.claim_heartbeat_at.is_(None),
                    TestRun.claim_heartbeat_at < stale_before,
                ),
            )
            .order_by(TestRun.created_at.asc(), TestRun.id.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
    ).scalar_one_or_none()
    if run is None:
        return None

    run.claimed_by = worker_id
    run.claimed_at = now
    run.claim_heartbeat_at = now
    await db.commit()
    await db.refresh(run)
    return run


async def heartbeat_claim(db: AsyncSession, run: TestRun) -> None:
    run.claim_heartbeat_at = datetime.now(timezone.utc)
    await db.commit()
