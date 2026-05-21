from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.platform import runtime


def test_ensure_runtime_dirs_creates_all_configured_storage_roots(
    monkeypatch, tmp_path: Path
) -> None:
    configured_paths = {
        "data_root": tmp_path / "root",
        "dataset_root": tmp_path / "root" / "data" / "datasets",
        "dataset_metadata_root": tmp_path / "root" / "data" / "dataset-registry",
        "runtime_root": tmp_path / "root" / "runtime",
        "uploads_root": tmp_path / "root" / "data" / "uploads",
        "avatars_root": tmp_path / "root" / "data" / "uploads" / "avatars",
        "credential_storage_dir": tmp_path / "root" / "runtime" / "credentials",
        "worker_workdir_root": tmp_path / "root" / "runtime" / "workdir",
        "tmp_root": tmp_path / "root" / "tmp",
        "log_root": tmp_path / "root" / "logs",
    }
    monkeypatch.setattr(runtime, "settings", SimpleNamespace(**configured_paths))

    runtime.ensure_runtime_dirs()

    assert all(path.is_dir() for path in configured_paths.values())
