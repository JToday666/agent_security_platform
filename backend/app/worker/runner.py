"""Worker 执行循环入口。"""

from __future__ import annotations

import asyncio
import logging

from app.models.benchmark_run import TestRun
from app.modules.evaluations.lifecycle import (
    mark_run_failed,
    reconcile_expired_paused_runs,
)
from app.modules.evaluations.state_rules import TERMINAL_STATUSES
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal
from app.worker.claims import claim_next_run
from app.worker.processing import process_claimed_run

LOGGER = logging.getLogger(__name__)


async def _process_run_safely(run_id: int, worker_id: str) -> None:
    """Process one claimed run and downgrade unexpected errors to failed runs."""
    try:
        await process_claimed_run(run_id, worker_id)
    except Exception as exc:
        async with AsyncSessionLocal() as db:
            run = await db.get(TestRun, run_id)
            if run is not None and run.status not in TERMINAL_STATUSES:
                try:
                    await mark_run_failed(
                        db,
                        run,
                        final_reason=f"worker_error:{exc.__class__.__name__}",
                    )
                except Exception:
                    await db.rollback()
        LOGGER.exception("Worker failed while processing run", exc_info=exc)


async def run_worker_loop(worker_id: str) -> None:
    """持续轮询并执行可处理的评测任务。"""
    active_runs: dict[int, asyncio.Task[None]] = {}
    try:
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    await reconcile_expired_paused_runs(db)

                while len(active_runs) < max(1, settings.WORKER_MAX_ACTIVE_RUNS):
                    async with AsyncSessionLocal() as db:
                        run = await claim_next_run(db, worker_id)
                    if run is None:
                        break
                    if run.id in active_runs:
                        break
                    active_runs[run.id] = asyncio.create_task(
                        _process_run_safely(run.id, worker_id)
                    )

                if active_runs:
                    done, _ = await asyncio.wait(
                        active_runs.values(),
                        timeout=settings.WORKER_POLL_INTERVAL_SECONDS,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if done:
                        for run_id, task in list(active_runs.items()):
                            if task in done:
                                active_runs.pop(run_id, None)
                                await task
                else:
                    await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
            except Exception:
                LOGGER.exception("Worker loop iteration failed")
                await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
    finally:
        for task in active_runs.values():
            task.cancel()
        if active_runs:
            await asyncio.gather(*active_runs.values(), return_exceptions=True)
