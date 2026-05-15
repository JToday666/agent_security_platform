"""Filesystem preparation helpers for runtime execution."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.platform.config import settings
from app.worker.runtime.exceptions import RuntimePreparationError

DATA_ROOT: Path | None = None


@dataclass(slots=True)
class SampleRuntimeTarget:
    """Lightweight sample snapshot used by worker runtime helpers."""

    sample_db_id: int
    sample_id: str
    sample_name: str
    resource_path: str
    entry_path: str
    user_goal: str


@dataclass(slots=True)
class PreparedRuntime:
    """Resolved runtime workspace and execution metadata."""

    execution_id: int
    work_dir: Path
    project_root: Path
    sample_dir: Path
    runtime_dir: Path
    sample_subpath: str
    entry_url: str
    environment_ref: str
    probe_token: str
    port: int
    run_dir: Path
    stdout_log: Path
    stderr_log: Path
    runtime_context_path: Path
    isolation_mode: str = "process"


def resolve_sample_layout(sample: SampleRuntimeTarget) -> tuple[Path, Path, Path, Path]:
    """Return sample dir, scope root, runtime dir and relative sample subpath."""
    data_root = (DATA_ROOT or settings.dataset_root).resolve()
    sample_dir = (data_root / sample.resource_path).resolve()
    if not sample_dir.is_dir():
        raise RuntimePreparationError(
            f"sample directory not found: {sample.resource_path}"
        )
    if data_root not in sample_dir.parents and sample_dir != data_root:
        raise RuntimePreparationError(
            f"sample directory escapes data root: {sample.resource_path}"
        )

    scope_root = sample_dir
    while True:
        runtime_dir = scope_root / "agent_runtime"
        if runtime_dir.is_dir():
            return (
                sample_dir,
                scope_root,
                runtime_dir,
                sample_dir.relative_to(scope_root),
            )
        if scope_root == data_root:
            break
        scope_root = scope_root.parent

    raise RuntimePreparationError(
        f"agent_runtime not found for sample: {sample.resource_path}"
    )


def build_environment_ref(execution_id: int) -> str:
    """Generate an opaque runtime instance id."""
    return f"rt_{execution_id}_{uuid4().hex[:8]}"


def build_probe_token() -> str:
    """Generate an opaque probe token."""
    return f"probe_tk_{uuid4().hex}"


def build_entry_url(host: str, port: int, sample_subpath: str, entry_path: str) -> str:
    """Build the browser entry URL served by the probe runner."""
    pieces = [
        piece.strip("/")
        for piece in (sample_subpath, entry_path)
        if piece and piece.strip("/")
    ]
    browser_path = "/".join(pieces)
    if not browser_path:
        raise RuntimePreparationError("entry path resolves to an empty browser URL")
    return f"http://{host}:{port}/{browser_path}"


def prepare_runtime_workspace(
    sample: SampleRuntimeTarget,
    execution_id: int,
    workdir_root: Path,
    host: str,
    port: int,
    environment_ref: str,
    probe_token: str,
) -> PreparedRuntime:
    """Prepare an isolated runtime workspace for one sample execution."""
    sample_dir, scope_root, runtime_dir, sample_subpath = resolve_sample_layout(sample)

    work_dir = (workdir_root / str(execution_id)).resolve()
    if work_dir.exists():
        shutil.rmtree(work_dir)
    project_root = work_dir / "project"
    project_root.mkdir(parents=True, exist_ok=True)

    sample_subpath_str = sample_subpath.as_posix()
    sample_dst = project_root / sample_subpath
    sample_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sample_dir, sample_dst)
    shutil.copytree(runtime_dir, project_root / "agent_runtime")

    run_dir = project_root / "agent_runtime" / "runs" / environment_ref
    run_dir.mkdir(parents=True, exist_ok=True)

    entry_url = build_entry_url(
        host=host,
        port=port,
        sample_subpath=sample_subpath_str,
        entry_path=sample.entry_path,
    )
    stdout_log = work_dir / "runner_stdout.log"
    stderr_log = work_dir / "runner_stderr.log"
    runtime_context_path = run_dir / "runtime_context.json"
    runtime_context_path.write_text(
        json.dumps(
            {
                "executionId": execution_id,
                "sampleId": sample.sample_id,
                "resourcePath": sample.resource_path,
                "entryPath": sample.entry_path,
                "browserEntryUrl": entry_url,
                "environmentRef": environment_ref,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return PreparedRuntime(
        execution_id=execution_id,
        work_dir=work_dir,
        project_root=project_root,
        sample_dir=sample_dir,
        runtime_dir=runtime_dir,
        sample_subpath=sample_subpath_str,
        entry_url=entry_url,
        environment_ref=environment_ref,
        probe_token=probe_token,
        port=port,
        run_dir=run_dir,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        runtime_context_path=runtime_context_path,
    )
