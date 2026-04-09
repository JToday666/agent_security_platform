from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
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
    stale_before = now
    candidates = (
        await db.execute(
            select(TestRun)
            .where(TestRun.status.in_(["pending", "running", "pausing", "terminating", "canceling"]))
            .order_by(TestRun.created_at.asc(), TestRun.id.asc())
            .with_for_update(skip_locked=True)
        )
    ).scalars()

    for run in candidates:
        if run.claimed_by is not None and run.claim_heartbeat_at is not None:
            if not claim_is_stale(run.claim_heartbeat_at, now=stale_before):
                continue
        run.claimed_by = worker_id
        run.claimed_at = now
        run.claim_heartbeat_at = now
        await db.commit()
        await db.refresh(run)
        return run

    return None


async def heartbeat_claim(db: AsyncSession, run: TestRun) -> None:
    run.claim_heartbeat_at = datetime.now(timezone.utc)
    await db.commit()
