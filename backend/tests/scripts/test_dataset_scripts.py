from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_NAMES = [
    "normalize_dataset_samples.py",
    "bootstrap_dataset_metadata_from_db.py",
    "generate_dataset_display_meta_index.py",
    "sync_dataset_registry_from_samples.py",
    "export_dataset_metadata_xlsx.py",
    "sync_dataset_metadata_from_xlsx.py",
    "import_dataset_metadata.py",
    "import_dataset_samples.py",
    "import_dataset_bundle.py",
    "import_datasets_demo.py",
]
SCRIPTS_REQUIRING_SAMPLE_ROOT = [
    "sync_dataset_registry_from_samples.py",
    "import_dataset_samples.py",
    "import_dataset_bundle.py",
    "import_datasets_demo.py",
]
SCRIPTS_REQUIRING_OUTPUT_DIR = [
    "normalize_dataset_samples.py",
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
    shutil.copytree(backend_root / "dataset_metadata", registry_root)

    bundle_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "import_dataset_bundle.py"),
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
    assert bundle_result.returncode == 0, bundle_result.stderr
    assert "validated" in bundle_result.stdout

    samples_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "import_dataset_samples.py"),
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
def test_sync_registry_and_demo_import_script_support_explicit_paths(
    backend_root: Path,
    repo_sample_bundle,
    tmp_path: Path,
) -> None:
    registry_root = tmp_path / "dataset_metadata"
    shutil.copytree(backend_root / "dataset_metadata", registry_root)

    sync_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "sync_dataset_registry_from_samples.py"),
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

    demo_result = subprocess.run(
        [
            sys.executable,
            str(backend_root / "scripts" / "import_datasets_demo.py"),
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
    assert demo_result.returncode == 0, demo_result.stderr
    assert "validated" in demo_result.stdout


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
            str(backend_root / "scripts" / "normalize_dataset_samples.py"),
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
            str(backend_root / "scripts" / "sync_dataset_registry_from_samples.py"),
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
            str(backend_root / "scripts" / "import_dataset_samples.py"),
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
