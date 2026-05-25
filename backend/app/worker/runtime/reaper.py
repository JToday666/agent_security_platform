"""Runtime container reaper for worker-managed Docker probe containers."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RuntimeSession
from app.modules.runtime_gateway.session_store import (
    expire_runtime_sessions_once,
    now_utc,
)
from app.platform.config import settings

LOGGER = logging.getLogger(__name__)

DOCKER_PS_FORMAT = (
    '{{.ID}}\t{{.Label "sampleExecutionId"}}\t{{.Label "environmentRef"}}'
)


@dataclass(slots=True)
class ManagedRuntimeContainer:
    """Docker container labels needed to decide whether a runtime is stale."""

    container_id: str
    sample_execution_id: int | None
    environment_ref: str | None


def _parse_sample_execution_id(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_managed_runtime_container_rows(text: str) -> list[ManagedRuntimeContainer]:
    """Parse `docker ps` rows for worker-managed runtime containers."""
    containers: list[ManagedRuntimeContainer] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        container_id = parts[0].strip()
        if not container_id:
            continue
        sample_execution_id = (
            _parse_sample_execution_id(parts[1].strip()) if len(parts) > 1 else None
        )
        environment_ref = (
            parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
        )
        containers.append(
            ManagedRuntimeContainer(
                container_id=container_id,
                sample_execution_id=sample_execution_id,
                environment_ref=environment_ref,
            )
        )
    return containers


async def _run_docker_command(*args: str) -> tuple[int, str, str]:
    try:
        process = await asyncio.create_subprocess_exec(
            "docker",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    stdout, stderr = await process.communicate()
    return (
        int(process.returncode or 0),
        stdout.decode("utf-8", errors="replace"),
        stderr.decode("utf-8", errors="replace"),
    )


async def list_managed_runtime_containers() -> list[ManagedRuntimeContainer]:
    """List currently running Docker runtime containers managed by asp-worker."""
    returncode, stdout, stderr = await _run_docker_command(
        "ps",
        "--filter",
        "label=managedBy=asp-worker",
        "--format",
        DOCKER_PS_FORMAT,
    )
    if returncode != 0:
        LOGGER.warning(
            "runtime_container_reaper_list_failed",
            extra={"return_code": returncode, "stderr": stderr[:500]},
        )
        return []
    return parse_managed_runtime_container_rows(stdout)


async def stop_runtime_container(container_id: str) -> None:
    """Stop one stale worker-managed runtime container."""
    returncode, _, stderr = await _run_docker_command("stop", container_id)
    if returncode != 0:
        LOGGER.warning(
            "runtime_container_reaper_stop_failed",
            extra={
                "container_id": container_id,
                "return_code": returncode,
                "stderr": stderr[:500],
            },
        )
        return
    LOGGER.info(
        "runtime_container_reaper_stopped",
        extra={"container_id": container_id},
    )


async def _active_runtime_session_ids(db: AsyncSession) -> set[int]:
    current_time = now_utc()
    rows = (
        await db.execute(
            select(RuntimeSession.sample_execution_id).where(
                RuntimeSession.status.in_(["preparing", "active"]),
                RuntimeSession.expires_at > current_time,
            )
        )
    ).scalars()
    return {int(sample_execution_id) for sample_execution_id in rows}


async def reap_runtime_containers_once(db: AsyncSession) -> int:
    """Stop worker-managed Docker runtime containers without an active session."""
    if not bool(settings.RUNTIME_CONTAINER_REAPER_ENABLED):
        return 0
    if settings.WORKER_RUNTIME_LAUNCH_MODE.strip().lower() != "docker":
        return 0

    await expire_runtime_sessions_once(db)
    active_session_ids = await _active_runtime_session_ids(db)
    containers = await list_managed_runtime_containers()
    stopped = 0
    for container in containers:
        if (
            container.sample_execution_id is not None
            and container.sample_execution_id in active_session_ids
        ):
            continue
        await stop_runtime_container(container.container_id)
        stopped += 1
    return stopped
