from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tests.helpers.scripts import load_module_from_path


@pytest.fixture(scope="module")
def prune_module(backend_root: Path):
    return load_module_from_path(
        "prune_storage_under_test", backend_root / "scripts" / "prune_storage.py"
    )


def _write_file(path: Path, text: str = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _set_mtime(path: Path, timestamp: datetime) -> None:
    value = timestamp.timestamp()
    os.utime(path, (value, value))


def _old_path(path: Path, *, now: datetime, days: int) -> Path:
    if path.suffix:
        _write_file(path)
    else:
        path.mkdir(parents=True, exist_ok=True)
        _write_file(path / "payload.txt")
    _set_mtime(path, now - timedelta(days=days))
    return path


def test_prune_storage_dry_run_reports_safe_candidates_without_deleting(
    prune_module, tmp_path: Path
) -> None:
    now = datetime(2026, 5, 28, tzinfo=timezone.utc)
    data_root = tmp_path / "asp"
    old_tmp = _old_path(data_root / "tmp" / "old-session", now=now, days=10)
    new_tmp = _old_path(data_root / "tmp" / "new-session", now=now, days=1)
    old_runtime = _old_path(
        data_root / "runtime" / "workdir" / "old-execution", now=now, days=20
    )
    old_rotated_log = _old_path(
        data_root / "logs" / "nginx" / "access.log.1", now=now, days=40
    )
    active_log = _old_path(data_root / "logs" / "nginx" / "access.log", now=now, days=40)
    old_artifact = _old_path(
        data_root / "artifacts" / "evaluations" / "123", now=now, days=300
    )

    candidates = prune_module.discover_candidates(
        prune_module.PruneConfig(data_root=data_root), now=now
    )
    result = prune_module.apply_prune(candidates, dry_run=True)

    assert result["dryRun"] is True
    assert result["candidateCount"] == 3
    assert {candidate.category for candidate in candidates} == {
        "tmp",
        "runtime_workdir",
        "rotated_log",
    }
    assert old_tmp.exists()
    assert new_tmp.exists()
    assert old_runtime.exists()
    assert old_rotated_log.exists()
    assert active_log.exists()
    assert old_artifact.exists()


def test_prune_storage_apply_can_include_old_artifacts(
    prune_module, tmp_path: Path
) -> None:
    now = datetime(2026, 5, 28, tzinfo=timezone.utc)
    data_root = tmp_path / "asp"
    old_tmp = _old_path(data_root / "tmp" / "old-session", now=now, days=10)
    old_artifact = _old_path(
        data_root / "artifacts" / "evaluations" / "123", now=now, days=300
    )

    candidates = prune_module.discover_candidates(
        prune_module.PruneConfig(data_root=data_root, include_artifacts=True),
        now=now,
    )
    result = prune_module.apply_prune(candidates, dry_run=False)

    assert result["dryRun"] is False
    assert result["deletedCount"] == 2
    assert not old_tmp.exists()
    assert not old_artifact.exists()


def test_prune_storage_refuses_project_checkout_roots(
    prune_module, backend_root: Path
) -> None:
    with pytest.raises(ValueError, match="inside project checkout"):
        prune_module.discover_candidates(
            prune_module.PruneConfig(data_root=backend_root / "tmp")
        )


def test_prune_storage_does_not_treat_filesystem_root_as_project_root(
    prune_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(prune_module, "BACKEND_ROOT", Path("/app"))
    data_root = tmp_path / "agent-security-platform"

    candidates = prune_module.discover_candidates(
        prune_module.PruneConfig(data_root=data_root)
    )

    assert candidates == []
