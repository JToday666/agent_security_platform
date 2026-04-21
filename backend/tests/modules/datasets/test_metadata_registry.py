from __future__ import annotations

from pathlib import Path

from app.modules.datasets.ingestion.metadata import load_metadata_bundle, sync_metadata_from_samples
from tests.helpers.dataset_bundle import write_json


def test_load_metadata_bundle_ignores_display_meta_index_file(tmp_path: Path) -> None:
    registry_root = tmp_path / "dataset_metadata"
    write_json(registry_root / "registry" / "dataset_sources.json", [])
    write_json(registry_root / "registry" / "attack_delivery_types.json", [])
    write_json(registry_root / "registry" / "asset_types.json", [])
    write_json(registry_root / "registry" / "risk_categories.json", [])
    write_json(registry_root / "registry" / "risk_subtypes.json", [])
    write_json(
        registry_root / "display_meta" / "A1_identity_leakage.json",
        {
            "subtype_code": "A1_identity_leakage",
            "short_description": "原有短描述",
            "full_description": "原有长描述",
            "highlights": [],
            "scenarios": [],
            "resources": [],
            "media": [],
        },
    )
    write_json(
        registry_root / "display_meta" / "index.json",
        [
            {
                "subtype_code": "A1_identity_leakage",
                "name": "身份信息泄露",
                "path": "display_meta/A1_identity_leakage.json",
            }
        ],
    )

    bundle = load_metadata_bundle(registry_root)

    assert sorted(bundle.display_meta_by_code) == ["A1_identity_leakage"]


def test_sync_registry_from_samples_adds_missing_entries_without_overwriting_existing_content(
    tmp_path: Path,
    repo_sample_bundle,
) -> None:
    registry_root = tmp_path / "dataset_metadata"
    write_json(
        registry_root / "registry" / "risk_categories.json",
        [
            {
                "code": "confidentiality",
                "name": "保留中的机密性名称",
                "meaning": "保留中的 meaning",
                "description": "保留中的 description",
                "sort_order": 9,
                "is_active": True,
            }
        ],
    )
    write_json(
        registry_root / "display_meta" / "A1_identity_leakage.json",
        {
            "subtype_code": "A1_identity_leakage",
            "short_description": "原有短描述",
            "full_description": "原有长描述",
            "highlights": [],
            "scenarios": [],
            "resources": [],
            "media": [],
        },
    )

    sync_metadata_from_samples(repo_sample_bundle.sample_root, registry_root)
    bundle = load_metadata_bundle(registry_root)

    assert len(bundle.dataset_sources) == repo_sample_bundle.dataset_source_count
    assert len(bundle.attack_delivery_types) == repo_sample_bundle.attack_delivery_count
    assert len(bundle.asset_types) == repo_sample_bundle.asset_type_count
    assert len(bundle.risk_categories) == repo_sample_bundle.category_count
    assert len(bundle.risk_subtypes) == repo_sample_bundle.subtype_count
    assert len(bundle.display_meta_by_code) == repo_sample_bundle.subtype_count

    confidentiality = next(item for item in bundle.risk_categories if item.code == "confidentiality")
    assert confidentiality.name == "保留中的机密性名称"
    assert confidentiality.meaning == "保留中的 meaning"
    assert bundle.display_meta_by_code["A1_identity_leakage"].short_description == "原有短描述"
    assert (registry_root / "display_meta" / "B2_cloud_file_modification.json").exists()

    index_path = registry_root / "display_meta" / "index.json"
    assert index_path.exists()
    index_payload = load_metadata_bundle(registry_root)
    assert len(index_payload.display_meta_by_code) == repo_sample_bundle.subtype_count
