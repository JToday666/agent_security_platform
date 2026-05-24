"""Worker process heartbeat and observability helpers."""

from __future__ import annotations

import os
import socket
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.worker_process import WorkerProcess


def now_utc() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


async def heartbeat_worker_process(
    db: AsyncSession,
    *,
    worker_id: str,
    role: str,
    active_count: int,
    metadata: dict[str, object],
) -> WorkerProcess:
    """Create or refresh one scheduler/sample-worker process heartbeat."""
    current_time = now_utc()
    row = (
        await db.execute(
            select(WorkerProcess).where(WorkerProcess.worker_id == worker_id)
        )
    ).scalar_one_or_none()
    if row is None:
        row = WorkerProcess(
            worker_id=worker_id,
            role=role,
            hostname=socket.gethostname(),
            pid=os.getpid(),
            status="healthy",
            started_at=current_time,
            last_heartbeat_at=current_time,
            active_count=max(0, active_count),
            process_metadata=metadata,
        )
        db.add(row)
    else:
        row.role = role
        row.hostname = socket.gethostname()
        row.pid = os.getpid()
        row.status = "healthy"
        row.last_heartbeat_at = current_time
        row.active_count = max(0, active_count)
        row.process_metadata = metadata
        row.updated_at = current_time
    await db.commit()
    await db.refresh(row)
    return row


async def mark_worker_stopped(db: AsyncSession, *, worker_id: str) -> bool:
    """Mark a worker process as stopped on graceful shutdown."""
    row = (
        await db.execute(
            select(WorkerProcess).where(WorkerProcess.worker_id == worker_id)
        )
    ).scalar_one_or_none()
    if row is None:
        return False
    row.status = "stopped"
    row.updated_at = now_utc()
    await db.commit()
    return True
