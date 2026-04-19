"""Artifact collection helpers for runtime executions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.worker.runtime.preparation import PreparedRuntime


@dataclass(slots=True)
class ArtifactRecord:
    """Normalized artifact ready to persist."""

    artifact_type: str
    path: Path
    storage_uri: str
    metadata: dict[str, object]


def _artifact_record(execution_id: int, root: Path, path: Path, artifact_type: str) -> ArtifactRecord:
    relative_path = path.relative_to(root).as_posix()
    stat = path.stat()
    return ArtifactRecord(
        artifact_type=artifact_type,
        path=path,
        storage_uri=f"runtime://executions/{execution_id}/{relative_path}",
        metadata={
            "relativePath": relative_path,
            "sizeBytes": stat.st_size,
        },
    )


def collect_artifacts(prepared: PreparedRuntime) -> list[ArtifactRecord]:
    """Collect runtime artifacts that should be indexed in the database."""
    records: list[ArtifactRecord] = []
    root = prepared.work_dir
    candidates = [
        (prepared.run_dir / "dispatch_context.json", "dispatch_context"),
        (prepared.run_dir / "runtime_context.json", "runtime_meta"),
        (prepared.run_dir / "meta.json", "runtime_meta"),
        (prepared.run_dir / "events.jsonl", "event_log"),
        (prepared.run_dir / "finalize.json", "finalize_payload"),
        (prepared.run_dir / "compile_result.json", "compile_result"),
        (prepared.run_dir / "replay_result.json", "replay_result"),
        (prepared.run_dir / "replay_artifacts" / "report.html", "replay_report"),
        (prepared.run_dir / "replay_artifacts" / "trace.zip", "replay_trace"),
        (prepared.run_dir / "replay_artifacts" / "replay.webm", "replay_video"),
        (prepared.run_dir / "replay_artifacts" / "final.png", "screenshot"),
        (prepared.stdout_log, "stdout_log"),
        (prepared.stderr_log, "stderr_log"),
    ]
    for path, artifact_type in candidates:
        if path.exists() and path.is_file():
            records.append(_artifact_record(prepared.execution_id, root=root, path=path, artifact_type=artifact_type))
    return records
