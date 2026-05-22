from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.modules.datasets.ingestion import pipeline
from app.modules.datasets.ingestion.types import NormalizationResult


def test_raw_import_workspace_defaults_to_configured_tmp_root(
    monkeypatch, tmp_path: Path
) -> None:
    sample_root = tmp_path / "samples"
    registry_root = tmp_path / "registry"
    configured_tmp_root = tmp_path / "asp-tmp"
    captured: dict[str, Path] = {}

    monkeypatch.setattr(pipeline, "settings", SimpleNamespace(tmp_root=configured_tmp_root))
    monkeypatch.setattr(
        pipeline, "detect_sample_root_kind", lambda source_root, mode: "raw"
    )

    def fake_normalize_sample_bundle(
        input_root: Path, output_root: Path, mode: str, dry_run: bool
    ) -> NormalizationResult:
        captured["input_root"] = input_root
        captured["output_root"] = output_root
        return NormalizationResult(input_root=input_root, output_root=output_root)

    monkeypatch.setattr(pipeline, "normalize_sample_bundle", fake_normalize_sample_bundle)
    monkeypatch.setattr(
        pipeline,
        "build_sample_import_plan",
        lambda effective_sample_root, mode: SimpleNamespace(samples=[]),
    )
    monkeypatch.setattr(
        pipeline,
        "build_metadata_bundle_from_samples",
        lambda effective_sample_root, registry_root, mode: object(),
    )

    result = pipeline.run_import_pipeline(
        sample_root=sample_root,
        registry_root=registry_root,
        mode="auto",
        dry_run=True,
    )

    assert captured["input_root"] == sample_root.resolve()
    assert captured["output_root"].name == "normalized_samples"
    assert captured["output_root"].parent.name.startswith("dataset_import_workspace_")
    assert captured["output_root"].parent.parent == configured_tmp_root
    assert result.effective_sample_root == captured["output_root"]
