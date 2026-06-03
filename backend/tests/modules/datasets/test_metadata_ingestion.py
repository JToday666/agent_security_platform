from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.benchmark import (
    AssetType,
    AttackDeliveryType,
    DatasetSource,
    RiskCategory,
    RiskSubtype,
    RiskSubtypeDisplayMeta,
)
from app.modules.datasets.ingestion.metadata import (
    _merge_default_attack_scenarios,
    apply_metadata_bundle,
    build_metadata_bundle_from_database,
)
from app.modules.datasets.ingestion.errors import ImportValidationError
from app.modules.datasets.ingestion.types import (
    AttackScenarioRecord,
    AssetTypeRecord,
    AttackDeliveryTypeRecord,
    DatasetSourceRecord,
    DisplayMetaRecord,
    MetadataBundle,
    RiskCategoryRecord,
    RiskSubtypeRecord,
)


def test_metadata_ingestion_persists_and_exports_localized_display_metadata(
    db_session,
) -> None:
    suffix = uuid4().hex[:8]
    category_code = f"pytest_i18n_category_{suffix}"
    subtype_code = f"pytest_i18n_subtype_{suffix}"
    source_code = f"pytest_i18n_source_{suffix}"
    delivery_code = f"pytest_i18n_delivery_{suffix}"
    asset_code = f"pytest_i18n_asset_{suffix}"
    bundle = MetadataBundle(
        attack_scenarios=[
            AttackScenarioRecord(
                code="prompt_injection",
                name="提示注入",
                description="覆盖提示注入攻击。",
                translations={
                    "en-US": {
                        "name": "Prompt Injection",
                        "description": "Prompt injection attacks.",
                    }
                },
            )
        ],
        dataset_sources=[
            DatasetSourceRecord(
                code=source_code,
                name="测试来源",
                description="测试来源描述。",
                translations={
                    "fr-FR": {
                        "name": "Source de test",
                        "description": "Description de la source de test.",
                    }
                },
            )
        ],
        attack_delivery_types=[
            AttackDeliveryTypeRecord(
                code=delivery_code,
                name="测试投递方式",
                description="测试投递方式描述。",
                translations={
                    "fr-FR": {
                        "name": "Mode de livraison de test",
                        "description": "Description du mode de livraison de test.",
                    }
                },
            )
        ],
        asset_types=[
            AssetTypeRecord(
                code=asset_code,
                name="测试资产",
                description="测试资产描述。",
                translations={
                    "fr-FR": {
                        "name": "Actif de test",
                        "description": "Description de l’actif de test.",
                    }
                },
            )
        ],
        risk_categories=[
            RiskCategoryRecord(
                code=category_code,
                name="机密性",
                meaning="保护敏感信息。",
                description="敏感信息暴露相关风险。",
                translations={
                    "en-US": {
                        "name": "Confidentiality",
                        "meaning": "Protect sensitive information.",
                        "description": "Risks related to sensitive information exposure.",
                    }
                },
            )
        ],
        risk_subtypes=[
            RiskSubtypeRecord(
                code=subtype_code,
                category_code=category_code,
                attack_scenario_code="prompt_injection",
                name="身份泄露",
                translations={"en-US": {"name": "Identity Leakage"}},
            )
        ],
        display_meta_by_code={
            subtype_code: DisplayMetaRecord(
                subtype_code=subtype_code,
                short_description="短描述",
                full_description="完整描述",
                highlights=["亮点"],
                scenarios=["场景"],
                resources=[{"label": "文档", "url": "https://example.com"}],
                media=[{"mediaId": "demo", "title": "示意图"}],
                translations={
                    "en-US": {
                        "short_description": "Short English description.",
                        "full_description": "Full English description.",
                        "highlights": ["English highlight"],
                        "scenarios": ["English scenario"],
                        "resources": [
                            {"label": "Docs", "url": "https://example.com"}
                        ],
                        "media": [{"mediaId": "demo", "title": "Diagram"}],
                    }
                },
            )
        },
    )

    result = apply_metadata_bundle(db_session, bundle)

    source = db_session.execute(
        select(DatasetSource).where(DatasetSource.code == source_code)
    ).scalar_one()
    delivery = db_session.execute(
        select(AttackDeliveryType).where(AttackDeliveryType.code == delivery_code)
    ).scalar_one()
    asset = db_session.execute(
        select(AssetType).where(AssetType.code == asset_code)
    ).scalar_one()
    category = db_session.execute(
        select(RiskCategory).where(RiskCategory.code == category_code)
    ).scalar_one()
    subtype = db_session.execute(
        select(RiskSubtype).where(RiskSubtype.code == subtype_code)
    ).scalar_one()
    display_meta = db_session.execute(
        select(RiskSubtypeDisplayMeta).where(
            RiskSubtypeDisplayMeta.subtype_id == subtype.id
        )
    ).scalar_one()
    exported = build_metadata_bundle_from_database(db_session)
    exported_source = next(
        item for item in exported.dataset_sources if item.code == source_code
    )
    exported_delivery = next(
        item for item in exported.attack_delivery_types if item.code == delivery_code
    )
    exported_asset = next(item for item in exported.asset_types if item.code == asset_code)
    exported_category = next(
        item for item in exported.risk_categories if item.code == category_code
    )
    exported_subtype = next(
        item for item in exported.risk_subtypes if item.code == subtype_code
    )
    exported_display_meta = exported.display_meta_by_code[subtype_code]

    assert result.created_sources == 1
    assert result.created_attack_scenarios == 1
    assert result.created_delivery_types == 1
    assert result.created_asset_types == 1
    assert result.created_categories == 1
    assert result.created_subtypes == 1
    assert result.created_display_meta == 1
    assert source.name == "测试来源"
    assert delivery.name == "测试投递方式"
    assert asset.name == "测试资产"
    assert exported_source.name == source.name
    assert exported_delivery.name == delivery.name
    assert exported_asset.name == asset.name
    assert source.translations["fr-FR"]["name"] == "Source de test"
    assert delivery.translations["fr-FR"]["name"] == "Mode de livraison de test"
    assert asset.translations["fr-FR"]["name"] == "Actif de test"
    assert exported_source.translations == source.translations
    assert exported_delivery.translations == delivery.translations
    assert exported_asset.translations == asset.translations
    assert category.translations["en-US"]["name"] == "Confidentiality"
    assert subtype.attack_scenario_id is not None
    assert subtype.translations["en-US"]["name"] == "Identity Leakage"
    assert (
        display_meta.translations["en-US"]["short_description"]
        == "Short English description."
    )
    assert exported_category.translations == category.translations
    assert exported.attack_scenarios[0].translations["en-US"]["name"] == (
        "Prompt Injection"
    )
    assert exported_subtype.translations == subtype.translations
    assert exported_subtype.attack_scenario_code == "prompt_injection"
    assert exported_display_meta.translations == display_meta.translations


def test_metadata_ingestion_rejects_new_subtype_without_attack_scenario(
    db_session,
) -> None:
    suffix = uuid4().hex[:8]
    bundle = MetadataBundle(
        attack_scenarios=[
            AttackScenarioRecord(
                code="knowledge_base_poisoning",
                name="知识库投毒",
            )
        ],
        risk_categories=[
            RiskCategoryRecord(
                code=f"pytest_poison_category_{suffix}",
                name="知识库完整性",
            )
        ],
        risk_subtypes=[
            RiskSubtypeRecord(
                code=f"pytest_poison_subtype_{suffix}",
                category_code=f"pytest_poison_category_{suffix}",
                name="检索内容投毒",
            )
        ],
    )

    with pytest.raises(ImportValidationError, match="attack_scenario_code"):
        apply_metadata_bundle(db_session, bundle)


def test_metadata_ingestion_preserves_default_attack_scenario_translations() -> None:
    scenarios = {
        item.code: item
        for item in _merge_default_attack_scenarios(
            [
                AttackScenarioRecord(
                    code="prompt_injection",
                    name="提示注入",
                    description="覆盖直接和间接提示注入攻击。",
                    sort_order=1,
                )
            ]
        )
    }

    assert scenarios["prompt_injection"].translations["en-US"]["name"] == (
        "Prompt Injection"
    )
    assert scenarios["model_abuse_and_unauthorized_actions"].translations["en-US"][
        "name"
    ] == "Model Abuse and Unauthorized Actions"
    assert scenarios["knowledge_base_poisoning"].translations["en-US"]["name"] == (
        "Knowledge Base Poisoning"
    )
    assert scenarios["tool_call_hijacking"].translations["en-US"]["name"] == (
        "Tool Call Hijacking"
    )
