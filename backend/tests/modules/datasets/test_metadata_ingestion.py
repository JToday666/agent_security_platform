from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from app.models.benchmark import (
    RiskCategory,
    RiskSubtype,
    RiskSubtypeDisplayMeta,
)
from app.modules.datasets.ingestion.metadata import (
    apply_metadata_bundle,
    build_metadata_bundle_from_database,
)
from app.modules.datasets.ingestion.types import (
    DisplayMetaRecord,
    MetadataBundle,
    RiskCategoryRecord,
    RiskSubtypeRecord,
)


def test_metadata_ingestion_persists_and_exports_translations(db_session) -> None:
    suffix = uuid4().hex[:8]
    category_code = f"pytest_i18n_category_{suffix}"
    subtype_code = f"pytest_i18n_subtype_{suffix}"
    bundle = MetadataBundle(
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
    exported_category = next(
        item for item in exported.risk_categories if item.code == category_code
    )
    exported_subtype = next(
        item for item in exported.risk_subtypes if item.code == subtype_code
    )
    exported_display_meta = exported.display_meta_by_code[subtype_code]

    assert result.created_categories == 1
    assert result.created_subtypes == 1
    assert result.created_display_meta == 1
    assert category.translations["en-US"]["name"] == "Confidentiality"
    assert subtype.translations["en-US"]["name"] == "Identity Leakage"
    assert (
        display_meta.translations["en-US"]["short_description"]
        == "Short English description."
    )
    assert exported_category.translations == category.translations
    assert exported_subtype.translations == subtype.translations
    assert exported_display_meta.translations == display_meta.translations
