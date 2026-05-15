from __future__ import annotations

from pathlib import Path

from app.modules.datasets.ingestion.pipeline import run_import_pipeline


def test_run_import_pipeline_skips_normalization_for_standard_input(
    repo_sample_bundle,
    tmp_path: Path,
) -> None:
    registry_root = tmp_path / "dataset_metadata"

    result = run_import_pipeline(
        sample_root=repo_sample_bundle.sample_root,
        registry_root=registry_root,
        dry_run=True,
    )

    assert result.input_kind == "standard"
    assert result.normalized is False
    assert result.sample_plan.sample_root == repo_sample_bundle.sample_root.resolve()
    assert result.sample_count == repo_sample_bundle.sample_count
    assert not registry_root.exists()


def test_run_import_pipeline_normalizes_raw_input_and_keeps_registry_pristine_on_dry_run(
    raw_sample_bundle,
    tmp_path: Path,
) -> None:
    registry_root = tmp_path / "dataset_metadata"
    workspace_dir = tmp_path / "workspace"

    result = run_import_pipeline(
        sample_root=raw_sample_bundle.sample_root,
        registry_root=registry_root,
        workspace_dir=workspace_dir,
        dry_run=True,
    )

    assert result.input_kind == "raw"
    assert result.normalized is True
    assert result.sample_count == raw_sample_bundle.sample_count
    assert (
        result.sample_plan.sample_root
        == (workspace_dir / "normalized_samples").resolve()
    )
    assert not registry_root.exists()
