"""Concurrency controls for worker runtime processes."""

from __future__ import annotations

import asyncio

from app.platform.config import settings


_RUNTIME_PROCESS_SEMAPHORE: asyncio.Semaphore | None = None
_RUNTIME_PROCESS_SEMAPHORE_LIMIT: int | None = None


def runtime_process_semaphore() -> asyncio.Semaphore:
    """Return the lazily resized global runtime process semaphore."""
    global _RUNTIME_PROCESS_SEMAPHORE
    global _RUNTIME_PROCESS_SEMAPHORE_LIMIT
    limit = max(1, int(settings.WORKER_MAX_ACTIVE_RUNTIME_PROCESSES))
    if _RUNTIME_PROCESS_SEMAPHORE is None or _RUNTIME_PROCESS_SEMAPHORE_LIMIT != limit:
        _RUNTIME_PROCESS_SEMAPHORE = asyncio.Semaphore(limit)
        _RUNTIME_PROCESS_SEMAPHORE_LIMIT = limit
    return _RUNTIME_PROCESS_SEMAPHORE

