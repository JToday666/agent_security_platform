"""Probe runner 进程生命周期工具，负责启动、探活与关闭 runtime。"""

from __future__ import annotations

import asyncio
import contextlib
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import IO

import httpx

from app.platform.config import settings
from app.worker.runtime.exceptions import RuntimeStartupError
from app.worker.runtime.preparation import PreparedRuntime

SHARED_PROBE_BACKEND = Path(__file__).resolve().with_name("probe_backend.py")


@dataclass(slots=True)
class RuntimeProcessHandle:
    """描述已启动 probe runner 进程及其关联句柄。"""

    prepared: PreparedRuntime
    process: asyncio.subprocess.Process
    stdout_handle: IO[str]
    stderr_handle: IO[str]


def runtime_base_url(prepared: PreparedRuntime) -> str:
    """返回当前 runtime 对外暴露的基础访问地址。"""
    return f"http://{settings.WORKER_RUNNER_HOST}:{prepared.port}"


def _build_direct_command(prepared: PreparedRuntime) -> list[str]:
    """构造直接启动共享 probe backend 的命令。"""
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
    """按隔离模式构造最终的 probe runner 启动命令。"""
    if isolation_mode == "docker":
        return _build_docker_command(prepared)
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


def _build_docker_command(prepared: PreparedRuntime) -> list[str]:
    """Build a Docker CLI command for one short-lived probe runtime container."""
    container_root = settings.WORKER_RUNTIME_DOCKER_CONTAINER_WORKDIR.rstrip("/")
    project_root = f"{container_root}/project"
    name = f"asp-runtime-{prepared.environment_ref}"
    return [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--network",
        settings.WORKER_RUNTIME_DOCKER_NETWORK,
        "-p",
        f"{settings.WORKER_RUNNER_HOST}:{prepared.port}:{prepared.port}",
        "-v",
        f"{prepared.work_dir}:{container_root}",
        "-w",
        container_root,
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=256",
        f"--cpus={settings.WORKER_RUNTIME_DOCKER_CPUS}",
        f"--memory={settings.WORKER_RUNTIME_DOCKER_MEMORY}",
        settings.WORKER_RUNTIME_DOCKER_IMAGE,
        "python",
        "-m",
        "app.worker.runtime.probe_backend",
        "--project-root",
        project_root,
        "--host",
        "0.0.0.0",
        "--port",
        str(prepared.port),
        "--instance-id",
        prepared.environment_ref,
        "--probe-token",
        prepared.probe_token,
    ]


def candidate_isolation_modes() -> list[str]:
    """Return launch modes ordered by preference."""
    if settings.WORKER_RUNTIME_LAUNCH_MODE.strip().lower() == "docker":
        return ["docker"]
    if settings.WORKER_NAMESPACE_ISOLATION_ENABLED and shutil.which("unshare"):
        return ["namespace", "process"]
    return ["process"]


async def _wait_until_healthy(
    handle: RuntimeProcessHandle, timeout_seconds: float
) -> None:
    """轮询健康检查接口，直到 probe runner 可用或超时。"""
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
                raise RuntimeStartupError(
                    f"probe runner health check timed out: {health_url}"
                )
            await asyncio.sleep(0.25)


async def _spawn_process(
    prepared: PreparedRuntime, isolation_mode: str
) -> RuntimeProcessHandle:
    """启动单个 probe runner 进程并返回运行句柄。"""
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
            await _wait_until_healthy(
                handle, settings.WORKER_RUNNER_START_TIMEOUT_SECONDS
            )
            return handle
        except Exception as exc:
            last_error = exc
            await stop_runtime(handle)

    raise RuntimeStartupError(str(last_error or "probe runner failed to start"))


async def request_runtime_close(
    handle: RuntimeProcessHandle, reason: str = "worker_shutdown"
) -> None:
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
                await asyncio.wait_for(
                    handle.process.wait(),
                    timeout=(
                        settings.WORKER_RUNTIME_DOCKER_STOP_TIMEOUT_SECONDS
                        if handle.prepared.isolation_mode == "docker"
                        else 5.0
                    ),
                )
            except asyncio.TimeoutError:
                handle.process.kill()
                await handle.process.wait()
    finally:
        with contextlib.suppress(Exception):
            handle.stdout_handle.close()
        with contextlib.suppress(Exception):
            handle.stderr_handle.close()
