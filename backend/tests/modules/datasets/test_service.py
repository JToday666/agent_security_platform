from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.modules.datasets.service import DatasetService
from app.platform.i18n import set_current_locale


class DatasetRow:
    def __init__(
        self,
        category,
        subtype,
        display_meta,
        sample_count: int,
        sample_updated_at: datetime,
    ) -> None:
        self.category = category
        self.subtype = subtype
        self.display_meta = display_meta
        self.sample_count = sample_count
        self.sample_updated_at = sample_updated_at

    def __iter__(self):
        yield self.category
        yield self.subtype
        yield self.display_meta
        yield self.sample_count
        yield self.sample_updated_at


class DatasetRepositoryStub:
    def __init__(self, category, subtype, display_meta) -> None:
        self.category = category
        self.subtype = subtype
        self.display_meta = display_meta

    async def get_catalog_rows(self):
        return [
            DatasetRow(
                self.category,
                self.subtype,
                self.display_meta,
                3,
                self.display_meta.updated_at,
            )
        ]

    async def get_detail_row(self, dataset_id: str):
        return DatasetRow(
            self.category,
            self.subtype,
            self.display_meta,
            3,
            self.display_meta.updated_at,
        )

    async def load_translation_maps(
        self, locale: str, category_ids: list[int], subtype_ids: list[int]
    ):
        return {
            "categories": {
                self.category.id: {
                    "name": "Confidentiality",
                    "meaning": "Protect sensitive information.",
                    "description": "Risks related to sensitive information exposure.",
                }
            },
            "subtypes": {
                self.subtype.id: {
                    "name": "Identity Leakage",
                }
            },
            "display_meta": {
                self.subtype.id: {
                    "short_description": "Short English description.",
                    "full_description": "Full English description.",
                    "highlights": ["English highlight"],
                    "scenarios": ["English scenario"],
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
                            "description": "English media description.",
                            "url": "https://example.com/image.png",
                        }
                    ],
                }
            },
        }


@pytest.mark.asyncio
async def test_dataset_catalog_and_detail_apply_locale_translation_fields() -> None:
    now = datetime.now(timezone.utc)
    category = SimpleNamespace(
        id=1,
        code="confidentiality",
        name="机密性",
        meaning="保护敏感信息。",
        description="敏感信息暴露相关风险。",
        sort_order=1,
        is_active=True,
        updated_at=now,
    )
    subtype = SimpleNamespace(
        id=2, code="A1_identity_leakage", name="身份泄露", is_active=True, sort_order=1
    )
    display_meta = SimpleNamespace(
        subtype_id=2,
        short_description="短描述",
        full_description="完整描述",
        highlights=["亮点"],
        scenarios=["场景"],
        resources=[
            {"label": "文档", "url": "https://example.com/docs", "type": "docs"}
        ],
        media=[
            {
                "mediaId": "demo",
                "type": "image",
                "title": "示意图",
                "description": "中文说明",
                "url": "https://example.com/image.png",
            }
        ],
        updated_at=now,
    )
    token = set_current_locale("en-US")
    try:
        service = DatasetService(DatasetRepositoryStub(category, subtype, display_meta))
        catalog = await service.get_catalog()
        detail = await service.get_detail("A1_identity_leakage")
    finally:
        token.reset()

    assert catalog.categories[0].name == "Confidentiality"
    assert catalog.categories[0].meaning == "Protect sensitive information."
    assert (
        catalog.categories[0].description
        == "Risks related to sensitive information exposure."
    )
    assert catalog.categories[0].subcategories[0].name == "Identity Leakage"
    assert (
        catalog.categories[0].subcategories[0].short_description
        == "Short English description."
    )
    assert detail.name == "Identity Leakage"
    assert detail.category.name == "Confidentiality"
    assert detail.full_description == "Full English description."
    assert detail.highlights == ["English highlight"]
    assert detail.resources[0]["label"] == "Docs"
    assert detail.media[0]["title"] == "Diagram"
