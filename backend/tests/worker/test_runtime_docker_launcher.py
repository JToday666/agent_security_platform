from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.worker.runtime import process as runtime_process
from app.worker.runtime.preparation import PreparedRuntime

pytestmark = pytest.mark.worker


def _prepared(tmp_path: Path) -> PreparedRuntime:
    work_dir = tmp_path / "workdir" / "101"
    project_root = work_dir / "project"
    sample_dir = project_root / "sample"
    runtime_dir = project_root / "agent_runtime"
    run_dir = runtime_dir / "runs" / "rt_101_test"
    run_dir.mkdir(parents=True)
    return PreparedRuntime(
        execution_id=101,
        run_id=77,
        work_dir=work_dir,
        project_root=project_root,
        sample_dir=sample_dir,
        runtime_dir=runtime_dir,
        sample_subpath="sample",
        entry_url="http://host.docker.internal:18101/index.html",
        environment_ref="rt_101_test",
        probe_token="probe-token",
        port=18101,
        run_dir=run_dir,
        stdout_log=work_dir / "runner_stdout.log",
        stderr_log=work_dir / "runner_stderr.log",
        runtime_context_path=run_dir / "runtime_context.json",
    )


def test_build_docker_command_mounts_single_workdir_and_limits_container(
    tmp_path: Path,
) -> None:
    prepared = _prepared(tmp_path)

    with (
        patch.object(runtime_process.settings, "WORKER_RUNNER_HOST", "172.17.0.1"),
        patch.object(
            runtime_process.settings,
            "WORKER_RUNTIME_DOCKER_IMAGE",
            "asp-runtime:latest",
            create=True,
        ),
        patch.object(
            runtime_process.settings,
            "WORKER_RUNTIME_DOCKER_CONTAINER_WORKDIR",
            "/runtime",
            create=True,
        ),
        patch.object(
            runtime_process.settings,
            "WORKER_RUNTIME_DOCKER_NETWORK",
            "asp-runtime-net",
            create=True,
        ),
        patch.object(
            runtime_process.settings,
            "WORKER_RUNTIME_DOCKER_PORT",
            8000,
            create=True,
        ),
        patch.object(
            runtime_process.settings,
            "WORKER_RUNTIME_DOCKER_CPUS",
            "1.0",
            create=True,
        ),
        patch.object(
            runtime_process.settings,
            "WORKER_RUNTIME_DOCKER_MEMORY",
            "1g",
            create=True,
        ),
    ):
        command = runtime_process._build_docker_command(prepared)

    assert command[:3] == ["docker", "run", "--rm"]
    assert "-p" not in command
    assert "--publish" not in command
    assert "--privileged" not in command
    assert "asp-runtime:latest" in command
    assert f"{prepared.work_dir}:/runtime" in command
    assert "/var/run/docker.sock" not in " ".join(command)
    assert command.count("-v") == 1
    assert command[command.index("-e") + 1] == "PYTHONPATH=/app"
    assert command[command.index("--network") + 1] == "asp-runtime-net"
    assert command[command.index("--network-alias") + 1] == "asp-runtime-rt_101_test"
    assert command[command.index("--name") + 1] == "asp-runtime-rt_101_test"
    assert "--label" in command
    assert "managedBy=asp-worker" in command
    assert "sampleExecutionId=101" in command
    assert "runId=77" in command
    assert "environmentRef=rt_101_test" in command
    assert "--cap-drop=ALL" in command
    assert "--security-opt=no-new-privileges" in command
    assert "--pids-limit=256" in command
    assert "--cpus=1.0" in command
    assert "--memory=1g" in command
    assert "/runtime/project" in command
    assert "--probe-token" in command
    assert command[command.index("--port") + 1] == "8000"
    image_index = command.index("asp-runtime:latest")
    assert command.index("-e") < image_index
    assert command[image_index + 1 : image_index + 4] == [
        "python",
        "-m",
        "app.worker.runtime.probe_backend",
    ]


@pytest.mark.asyncio
async def test_launch_runtime_uses_docker_launcher_when_configured(tmp_path: Path) -> None:
    prepared = _prepared(tmp_path)
    fake_process = SimpleNamespace(returncode=None, terminate=lambda: None)
    fake_process.wait = AsyncMock(return_value=0)
    fake_handle = runtime_process.RuntimeProcessHandle(
        prepared=prepared,
        process=fake_process,
        stdout_handle=SimpleNamespace(close=lambda: None),
        stderr_handle=SimpleNamespace(close=lambda: None),
    )

    with (
        patch.object(runtime_process.settings, "WORKER_RUNTIME_LAUNCH_MODE", "docker", create=True),
        patch.object(runtime_process, "_spawn_process", new=AsyncMock(return_value=fake_handle)) as spawn_mock,
        patch.object(runtime_process, "_wait_until_healthy", new=AsyncMock()) as health_mock,
    ):
        handle = await runtime_process.launch_runtime(prepared)

    assert handle.prepared is prepared
    assert handle.process is fake_process
    spawn_mock.assert_awaited_once_with(prepared, isolation_mode="docker")
    health_mock.assert_awaited_once()


def test_runtime_base_url_uses_internal_container_dns_for_docker_mode(
    tmp_path: Path,
) -> None:
    prepared = _prepared(tmp_path)
    prepared.isolation_mode = "docker"

    with patch.object(
        runtime_process.settings,
        "WORKER_RUNTIME_DOCKER_PORT",
        8000,
        create=True,
    ):
        assert (
            runtime_process.runtime_base_url(prepared)
            == "http://asp-runtime-rt_101_test:8000"
        )


def test_runtime_base_url_keeps_runner_host_and_allocated_port_for_process_mode(
    tmp_path: Path,
) -> None:
    prepared = _prepared(tmp_path)
    prepared.isolation_mode = "process"

    with patch.object(runtime_process.settings, "WORKER_RUNNER_HOST", "127.0.0.1"):
        assert runtime_process.runtime_base_url(prepared) == "http://127.0.0.1:18101"
