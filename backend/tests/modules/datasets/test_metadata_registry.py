from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.modules.datasets.ingestion.metadata import (
    load_metadata_bundle,
    sync_metadata_from_samples,
    write_metadata_bundle,
)
from tests.helpers.dataset_bundle import write_json, write_repo_like_sample_bundle


def workspace_tmp_path() -> Path:
    path = Path.cwd() / "runtime" / "test-metadata" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_load_metadata_bundle_ignores_display_meta_index_file() -> None:
    registry_root = workspace_tmp_path() / "dataset_metadata"
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


def test_metadata_bundle_preserves_translations_round_trip() -> None:
    root = workspace_tmp_path()
    registry_root = root / "dataset_metadata"
    write_json(
        registry_root / "registry" / "dataset_sources.json",
        [
            {
                "code": "demo_source",
                "name": "演示来源",
                "translations": {
                    "en-US": {
                        "name": "Demo Source",
                        "description": "Demo source description.",
                    }
                },
            }
        ],
    )
    write_json(registry_root / "registry" / "attack_delivery_types.json", [])
    write_json(registry_root / "registry" / "asset_types.json", [])
    write_json(
        registry_root / "registry" / "risk_categories.json",
        [
            {
                "code": "confidentiality",
                "name": "机密性",
                "meaning": "保护敏感信息。",
                "description": "敏感信息暴露相关风险。",
                "translations": {
                    "en-US": {
                        "name": "Confidentiality",
                        "meaning": "Protect sensitive information.",
                        "description": "Risks related to sensitive information exposure.",
                    }
                },
            }
        ],
    )
    write_json(
        registry_root / "registry" / "risk_subtypes.json",
        [
            {
                "code": "A1_identity_leakage",
                "category_code": "confidentiality",
                "name": "身份泄露",
                "translations": {"en-US": {"name": "Identity Leakage"}},
            }
        ],
    )
    write_json(
        registry_root / "display_meta" / "A1_identity_leakage.json",
        {
            "subtype_code": "A1_identity_leakage",
            "short_description": "短描述",
            "full_description": "完整描述",
            "highlights": ["亮点"],
            "scenarios": ["场景"],
            "resources": [
                {"label": "文档", "url": "https://example.com/docs", "type": "docs"}
            ],
            "media": [
                {
                    "mediaId": "demo",
                    "type": "image",
                    "title": "示意图",
                    "description": "中文说明",
                }
            ],
            "translations": {
                "en-US": {
                    "short_description": "Short description.",
                    "full_description": "Full description.",
                    "highlights": ["Highlight"],
                    "scenarios": ["Scenario"],
                    "resources": [
                        {
                            "label": "Docs",
                            "url": "https://example.com/docs",
                            "type": "docs",
                        }
                    ],
                    "media": [
                        {
                            "mediaId": "demo",
                            "type": "image",
                            "title": "Diagram",
                            "description": "English description.",
                        }
                    ],
                }
            },
        },
    )

    bundle = load_metadata_bundle(registry_root)
    output_root = root / "round_trip"
    write_metadata_bundle(output_root, bundle)
    round_tripped = load_metadata_bundle(output_root)

    assert (
        round_tripped.dataset_sources[0].translations["en-US"]["name"] == "Demo Source"
    )
    assert (
        round_tripped.risk_categories[0].translations["en-US"]["meaning"]
        == "Protect sensitive information."
    )
    assert (
        round_tripped.risk_subtypes[0].translations["en-US"]["name"]
        == "Identity Leakage"
    )
    assert (
        round_tripped.display_meta_by_code["A1_identity_leakage"].translations["en-US"][
            "media"
        ][0]["title"]
        == "Diagram"
    )


def test_sync_registry_from_samples_adds_missing_entries_without_overwriting_existing_content() -> (
    None
):
    root = workspace_tmp_path()
    repo_sample_bundle = write_repo_like_sample_bundle(root / "samples")
    registry_root = root / "dataset_metadata"
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

    confidentiality = next(
        item for item in bundle.risk_categories if item.code == "confidentiality"
    )
    assert confidentiality.name == "保留中的机密性名称"
    assert confidentiality.meaning == "保留中的 meaning"
    assert (
        bundle.display_meta_by_code["A1_identity_leakage"].short_description
        == "原有短描述"
    )
    assert (registry_root / "display_meta" / "B2_cloud_file_modification.json").exists()

    index_path = registry_root / "display_meta" / "index.json"
    assert index_path.exists()
    index_payload = load_metadata_bundle(registry_root)
    assert len(index_payload.display_meta_by_code) == repo_sample_bundle.subtype_count
