from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_NAMES = [
    "import_datasets.py",
    "datasets/normalize_samples.py",
    "datasets/standardize_task_json.py",
    "datasets/bootstrap_metadata_from_db.py",
    "datasets/sync_metadata_from_samples.py",
    "datasets/import_metadata.py",
    "datasets/import_samples.py",
]
SCRIPTS_REQUIRING_SAMPLE_ROOT = [
    "import_datasets.py",
    "datasets/sync_metadata_from_samples.py",
    "datasets/import_samples.py",
]
SCRIPTS_REQUIRING_OUTPUT_DIR = [
    "datasets/normalize_samples.py",
]


@pytest.mark.scripts
@pytest.mark.parametrize("script_name", SCRIPT_NAMES)
def test_expected_scripts_exist_and_support_help(backend_root: Path, script_name: str) -> None:
    script_path = backend_root / "scripts" / script_name

    assert script_path.exists(), f"{script_name} should exist"
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()


@pytest.mark.scripts
@pytest.mark.parametrize("script_name", SCRIPTS_REQUIRING_SAMPLE_ROOT)
def test_sample_root_scripts_require_explicit_sample_root(backend_root: Path, script_name: str) -> None:
    script_path = backend_root / "scripts" / script_name

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--sample-root" in result.stderr


@pytest.mark.scripts
@pytest.mark.parametrize("script_name", SCRIPTS_REQUIRING_OUTPUT_DIR)
def test_normalize_script_requires_explicit_output_dir(backend_root: Path, script_name: str) -> None:
    script_path = backend_root / "scripts" / script_name

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--output-dir" in result.stderr


@pytest.mark.scripts
def test_import_bundle_and_import_samples_support_explicit_paths(
    backend_root: Path,
    repo_sample_bundle,
    tmp_path: Path,
) -> None:
    registry_root = tmp_path / "dataset_metadata"
    pipeline_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "import_datasets.py"),
            "--sample-root",
            str(repo_sample_bundle.sample_root),
            "--registry-root",
            str(registry_root),
            "--dry-run",
        ],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )
    assert pipeline_result.returncode == 0, pipeline_result.stderr
    assert "input_kind=standard" in pipeline_result.stdout
    assert f"samples={repo_sample_bundle.sample_count}" in pipeline_result.stdout

    samples_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "datasets" / "import_samples.py"),
            "--sample-root",
            str(repo_sample_bundle.sample_root),
            "--dry-run",
        ],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )
    assert samples_result.returncode == 0, samples_result.stderr
    assert f"samples={repo_sample_bundle.sample_count}" in samples_result.stdout


@pytest.mark.scripts
def test_sync_registry_and_bundle_import_script_support_explicit_paths(
    backend_root: Path,
    repo_sample_bundle,
    tmp_path: Path,
) -> None:
    registry_root = tmp_path / "dataset_metadata"

    sync_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "datasets" / "sync_metadata_from_samples.py"),
            "--sample-root",
            str(repo_sample_bundle.sample_root),
            "--registry-root",
            str(registry_root),
        ],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )
    assert sync_result.returncode == 0, sync_result.stderr
    assert "display_meta=" in sync_result.stdout

    pipeline_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "import_datasets.py"),
            "--sample-root",
            str(repo_sample_bundle.sample_root),
            "--registry-root",
            str(registry_root),
            "--dry-run",
        ],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )
    assert pipeline_result.returncode == 0, pipeline_result.stderr
    assert "input_kind=standard" in pipeline_result.stdout


@pytest.mark.scripts
def test_normalize_script_generates_standard_bundle_consumable_by_sync_and_import(
    backend_root: Path,
    raw_sample_bundle,
    tmp_path: Path,
) -> None:
    normalized_root = tmp_path / "normalized_samples"
    normalize_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "datasets" / "normalize_samples.py"),
            "--input-root",
            str(raw_sample_bundle.sample_root),
            "--output-dir",
            str(normalized_root),
        ],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )
    assert normalize_result.returncode == 0, normalize_result.stderr
    assert f"samples={raw_sample_bundle.sample_count}" in normalize_result.stdout

    registry_root = tmp_path / "dataset_metadata"
    sync_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "datasets" / "sync_metadata_from_samples.py"),
            "--sample-root",
            str(normalized_root),
            "--registry-root",
            str(registry_root),
        ],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )
    assert sync_result.returncode == 0, sync_result.stderr
    assert "display_meta=" in sync_result.stdout

    import_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "datasets" / "import_samples.py"),
            "--sample-root",
            str(normalized_root),
            "--dry-run",
        ],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )
    assert import_result.returncode == 0, import_result.stderr
    assert f"samples={raw_sample_bundle.sample_count}" in import_result.stdout


@pytest.mark.scripts
def test_import_datasets_detects_raw_input_and_normalizes_into_workspace(
    backend_root: Path,
    raw_sample_bundle,
    tmp_path: Path,
) -> None:
    registry_root = tmp_path / "dataset_metadata"
    workspace_dir = tmp_path / "workspace"

    result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "import_datasets.py"),
            "--sample-root",
            str(raw_sample_bundle.sample_root),
            "--registry-root",
            str(registry_root),
            "--workspace-dir",
            str(workspace_dir),
            "--dry-run",
        ],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "input_kind=raw" in result.stdout
    assert "normalized=yes" in result.stdout
    assert (workspace_dir / "normalized_samples").exists()


@pytest.mark.scripts
def test_standardize_task_json_rewrites_only_task_json(
    backend_root: Path,
    raw_sample_bundle,
) -> None:
    task_path = raw_sample_bundle.sample_root / "01_Confidentiality" / "A3_Address_and_Location_Leakage" / "EIA_A3_10_high" / "task.json"
    sidecar_path = task_path.with_name("CarRentalse-Receipts.json")
    before_sidecar = sidecar_path.read_text(encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "datasets" / "standardize_task_json.py"),
            "--sample-root",
            str(raw_sample_bundle.sample_root),
            "--write",
        ],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "samples=2" in result.stdout
    assert "changed=1" in result.stdout
    assert '"schema_version": "1.0"' in task_path.read_text(encoding="utf-8")
    assert sidecar_path.read_text(encoding="utf-8") == before_sidecar
