"""Worker 执行循环入口。"""

from __future__ import annotations

import asyncio
import logging

from app.modules.evaluations.lifecycle import mark_run_failed, reconcile_expired_paused_runs
from app.shared.config import settings
from app.shared.db.session import AsyncSessionLocal
from app.worker.claims import claim_next_run, heartbeat_claim
from app.worker.processing import process_claimed_run


LOGGER = logging.getLogger(__name__)

async def run_worker_loop(worker_id: str) -> None:
    """持续轮询并执行可处理的评测任务。"""
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
