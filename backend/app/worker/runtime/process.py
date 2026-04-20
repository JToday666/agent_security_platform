"""Probe runner process lifecycle helpers."""

from __future__ import annotations

import asyncio
import contextlib
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import IO

import httpx

from app.shared.config import BACKEND_DIR, settings
from app.worker.runtime.exceptions import RuntimeStartupError
from app.worker.runtime.preparation import PreparedRuntime


SHARED_PROBE_BACKEND = BACKEND_DIR / "data" / "agent_runtime_shared" / "probe_backend.py"


@dataclass(slots=True)
class RuntimeProcessHandle:
    """Live probe runner process and associated metadata."""

    prepared: PreparedRuntime
    process: asyncio.subprocess.Process
    stdout_handle: IO[str]
    stderr_handle: IO[str]


def runtime_base_url(prepared: PreparedRuntime) -> str:
    """Return the runtime base URL."""
    return f"http://{settings.WORKER_RUNNER_HOST}:{prepared.port}"


def _build_direct_command(prepared: PreparedRuntime) -> list[str]:
    return [
        sys.executable,
        str(SHARED_PROBE_BACKEND),
        "--project-root",
        str(prepared.project_root),
        "--host",
        settings.WORKER_RUNNER_HOST,
        "--port",
        str(prepared.port),
        "--instance-id",
        prepared.environment_ref,
        "--probe-token",
        prepared.probe_token,
    ]


def _build_command(prepared: PreparedRuntime, isolation_mode: str) -> list[str]:
    direct = _build_direct_command(prepared)
    if isolation_mode != "namespace":
        return direct
    return [
        "unshare",
        "--mount",
        "--pid",
        "--ipc",
        "--uts",
        "--fork",
        *direct,
    ]


def candidate_isolation_modes() -> list[str]:
    """Return launch modes ordered by preference."""
    if settings.WORKER_NAMESPACE_ISOLATION_ENABLED and shutil.which("unshare"):
        return ["namespace", "process"]
    return ["process"]


async def _wait_until_healthy(handle: RuntimeProcessHandle, timeout_seconds: float) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    health_url = f"{runtime_base_url(handle.prepared)}/__probe__/health"
    async with httpx.AsyncClient(timeout=httpx.Timeout(1.0)) as client:
        while True:
            if handle.process.returncode is not None:
                raise RuntimeStartupError(
                    f"probe runner exited early with code {handle.process.returncode}"
                )
            try:
                response = await client.get(health_url)
                payload = response.json()
                if response.status_code == 200 and payload.get("code") == 0:
                    return
            except Exception:
                pass

            if asyncio.get_running_loop().time() >= deadline:
                raise RuntimeStartupError(f"probe runner health check timed out: {health_url}")
            await asyncio.sleep(0.25)


async def _spawn_process(prepared: PreparedRuntime, isolation_mode: str) -> RuntimeProcessHandle:
    prepared.isolation_mode = isolation_mode
    stdout_handle = prepared.stdout_log.open("w", encoding="utf-8")
    stderr_handle = prepared.stderr_log.open("w", encoding="utf-8")
    process = await asyncio.create_subprocess_exec(
        *_build_command(prepared, isolation_mode),
        cwd=str(prepared.project_root),
        stdout=stdout_handle,
        stderr=stderr_handle,
    )
    return RuntimeProcessHandle(
        prepared=prepared,
        process=process,
        stdout_handle=stdout_handle,
        stderr_handle=stderr_handle,
    )


async def launch_runtime(prepared: PreparedRuntime) -> RuntimeProcessHandle:
    """Launch the shared probe runner and wait until it becomes healthy."""
    last_error: Exception | None = None
    for isolation_mode in candidate_isolation_modes():
        handle = await _spawn_process(prepared, isolation_mode=isolation_mode)
        try:
            await _wait_until_healthy(handle, settings.WORKER_RUNNER_START_TIMEOUT_SECONDS)
            return handle
        except Exception as exc:
            last_error = exc
            await stop_runtime(handle)

    raise RuntimeStartupError(str(last_error or "probe runner failed to start"))


async def request_runtime_close(handle: RuntimeProcessHandle, reason: str = "worker_shutdown") -> None:
    """Ask the runtime to close and flush any pending evidence."""
    payload = {
        "instanceId": handle.prepared.environment_ref,
        "token": handle.prepared.probe_token,
        "reason": reason,
        "events": [],
        "meta": {},
    }
    url = f"{runtime_base_url(handle.prepared)}/__probe__/close"
    async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as client:
        with contextlib.suppress(Exception):
            await client.post(url, json=payload)


async def stop_runtime(handle: RuntimeProcessHandle, close_probe: bool = False) -> None:
    """Terminate the runtime process and release file handles."""
    try:
        if close_probe and handle.process.returncode is None:
            await request_runtime_close(handle)
        if handle.process.returncode is None:
            handle.process.terminate()
            try:
                await asyncio.wait_for(handle.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                handle.process.kill()
                await handle.process.wait()
    finally:
        with contextlib.suppress(Exception):
            handle.stdout_handle.close()
        with contextlib.suppress(Exception):
            handle.stderr_handle.close()
