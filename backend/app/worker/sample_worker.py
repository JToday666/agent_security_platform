"""Sample worker loop for executing claimed sample executions."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from types import SimpleNamespace

from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal
from app.worker.execution import execute_sample
from app.worker.execution_jobs import load_sample_job_by_execution_id
from app.worker.execution_persistence import mark_execution_system_error
from app.worker.processing import (
    resolve_dispatch_config,
    resolve_dispatch_mode,
    resolve_timeout_seconds,
)
from app.worker.sample_claims import claim_next_sample, heartbeat_sample_claim_by_id

LOGGER = logging.getLogger(__name__)


async def _heartbeat_loop(
    execution_id: int, worker_id: str, stop_event: asyncio.Event
) -> None:
    """Refresh the sample execution lease while a worker task is active."""
    while not stop_event.is_set():
        try:
            async with AsyncSessionLocal() as db:
                claimed = await heartbeat_sample_claim_by_id(db, execution_id, worker_id)
            if not claimed:
                return
        except Exception:
            LOGGER.exception(
                "Failed to heartbeat claimed sample execution",
                extra={"sample_execution_id": execution_id},
            )

        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=settings.SAMPLE_HEARTBEAT_INTERVAL_SECONDS
            )
        except asyncio.TimeoutError:
            continue


async def _process_sample_safely(execution_id: int, worker_id: str) -> None:
    """Execute one claimed sample and persist unexpected worker errors as sample errors."""
    loaded = await load_sample_job_by_execution_id(execution_id)
    if loaded is None:
        return

    run_snapshot = SimpleNamespace(
        public_id=loaded.run_public_id,
        execution_config=loaded.execution_config,
    )
    stop_event = asyncio.Event()
    heartbeat_task = asyncio.create_task(
        _heartbeat_loop(execution_id, worker_id, stop_event)
    )
    try:
        await execute_sample(
            loaded.run_id,
            loaded.dataset_id,
            loaded.job,
            dispatch_mode=resolve_dispatch_mode(run_snapshot),
            dispatch_config=resolve_dispatch_config(run_snapshot),
            timeout_seconds=resolve_timeout_seconds(run_snapshot),
        )
    except Exception as exc:
        await mark_execution_system_error(
            execution_id, loaded.run_id, loaded.dataset_id, exc
        )
        LOGGER.exception(
            "Sample worker failed while executing sample",
            extra={"sample_execution_id": execution_id},
        )
    finally:
        stop_event.set()
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task


async def run_sample_worker_loop(worker_id: str) -> None:
    """Continuously claim and execute ready sample executions."""
    active_executions: dict[int, asyncio.Task[None]] = {}
    try:
        while True:
            try:
                while len(active_executions) < max(
                    1, settings.SAMPLE_WORKER_MAX_ACTIVE_EXECUTIONS
                ):
                    async with AsyncSessionLocal() as db:
                        execution = await claim_next_sample(db, worker_id)
                    if execution is None:
                        break
                    if execution.id in active_executions:
                        break
                    active_executions[execution.id] = asyncio.create_task(
                        _process_sample_safely(execution.id, worker_id)
                    )

                if active_executions:
                    done, _ = await asyncio.wait(
                        active_executions.values(),
                        timeout=settings.WORKER_POLL_INTERVAL_SECONDS,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if done:
                        for execution_id, task in list(active_executions.items()):
                            if task in done:
                                active_executions.pop(execution_id, None)
                                await task
                else:
                    await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
            except Exception:
                LOGGER.exception("Sample worker loop iteration failed")
                await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
    finally:
        for task in active_executions.values():
            task.cancel()
        if active_executions:
            await asyncio.gather(*active_executions.values(), return_exceptions=True)
