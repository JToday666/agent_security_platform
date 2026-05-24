from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, or_, select

from app.models.worker_process import WorkerProcess
from app.platform.db.session import AsyncSessionLocal, engine as async_engine
from app.worker.observability import heartbeat_worker_process, mark_worker_stopped

pytestmark = pytest.mark.worker


@pytest_asyncio.fixture(autouse=True)
async def isolate_async_engine_pool_for_event_loop():
    await async_engine.dispose()
    await _cleanup_worker_observability_rows()
    yield
    await _cleanup_worker_observability_rows()
    await async_engine.dispose()


async def _cleanup_worker_observability_rows() -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(WorkerProcess).where(
                or_(
                    WorkerProcess.worker_id.like("worker-observe-test%"),
                    WorkerProcess.worker_id.like("worker-stop-test%"),
                    WorkerProcess.worker_id.like("worker-stale-test%"),
                )
            )
        )
        await db.commit()


@pytest.mark.asyncio
async def test_worker_heartbeat_upserts_process_row() -> None:
    worker_id = f"worker-observe-test-{uuid4().hex}"
    async with AsyncSessionLocal() as db:
        await heartbeat_worker_process(
            db,
            worker_id=worker_id,
            role="sample_worker",
            active_count=1,
            metadata={"loopErrors": 0},
        )

    async with AsyncSessionLocal() as db:
        worker = (
            await db.execute(
                select(WorkerProcess).where(
                    WorkerProcess.worker_id == worker_id
                )
            )
        ).scalar_one()

    assert worker.role == "sample_worker"
    assert worker.status == "healthy"
    assert worker.active_count == 1
    assert worker.last_heartbeat_at is not None
    assert worker.process_metadata == {"loopErrors": 0}


@pytest.mark.asyncio
async def test_mark_worker_stopped_updates_status() -> None:
    worker_id = f"worker-stop-test-{uuid4().hex}"
    async with AsyncSessionLocal() as db:
        await heartbeat_worker_process(
            db,
            worker_id=worker_id,
            role="scheduler",
            active_count=0,
            metadata={},
        )
        await mark_worker_stopped(db, worker_id=worker_id)

    async with AsyncSessionLocal() as db:
        worker = (
            await db.execute(
                select(WorkerProcess).where(
                    WorkerProcess.worker_id == worker_id
                )
            )
        ).scalar_one()

    assert worker.status == "stopped"


@pytest.mark.asyncio
async def test_stale_worker_alert_detects_old_heartbeat() -> None:
    worker_id = f"worker-stale-test-{uuid4().hex}"
    async with AsyncSessionLocal() as db:
        worker = WorkerProcess(
            worker_id=worker_id,
            role="scheduler",
            hostname="host",
            pid=999,
            status="healthy",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            last_heartbeat_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            active_count=0,
            process_metadata={},
        )
        db.add(worker)
        await db.commit()

        from app.modules.ops.service import build_worker_status

        status = await build_worker_status(db, stale_after_seconds=30)

    assert any(alert["type"] == "stale_worker" for alert in status["alerts"])
