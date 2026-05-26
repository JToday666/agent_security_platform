from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.modules.datasets.repository import DatasetRepository
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

    async def get_detail_sample_rows(self, dataset_id: str):
        return []

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


class EmptyTranslationRepositoryStub(DatasetRepositoryStub):
    async def load_translation_maps(
        self, locale: str, category_ids: list[int], subtype_ids: list[int]
    ):
        return {
            "categories": {
                self.category.id: {
                    "name": "",
                    "meaning": "",
                    "description": "",
                }
            },
            "subtypes": {
                self.subtype.id: {
                    "name": "",
                }
            },
            "display_meta": {
                self.subtype.id: {
                    "short_description": "",
                    "full_description": "",
                    "highlights": [],
                    "scenarios": [],
                    "resources": [],
                    "media": [],
                }
            },
        }


class ExecuteRows:
    def __init__(self, rows) -> None:
        self.rows = rows

    def all(self):
        return self.rows


class TranslationSessionStub:
    def __init__(self) -> None:
        self.results = [
            [
                (
                    1,
                    {
                        "en-US": {
                            "name": "Confidentiality",
                            "meaning": "Protect sensitive information.",
                        }
                    },
                )
            ],
            [(2, {"en-US": {"name": "Identity Leakage"}})],
            [
                (
                    2,
                    {"en-US": {"short_description": "Short English description."}},
                )
            ],
        ]

    async def execute(self, stmt):
        _ = stmt
        return ExecuteRows(self.results.pop(0))


@pytest.mark.asyncio
async def test_dataset_repository_loads_locale_translation_maps() -> None:
    repository = DatasetRepository(TranslationSessionStub())

    assert await repository.load_translation_maps("en-US", [1], [2]) == {
        "categories": {
            1: {
                "name": "Confidentiality",
                "meaning": "Protect sensitive information.",
            }
        },
        "subtypes": {2: {"name": "Identity Leakage"}},
        "display_meta": {2: {"short_description": "Short English description."}},
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


@pytest.mark.asyncio
async def test_empty_dataset_translations_do_not_override_default_content() -> None:
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
        service = DatasetService(
            EmptyTranslationRepositoryStub(category, subtype, display_meta)
        )
        catalog = await service.get_catalog()
        detail = await service.get_detail("A1_identity_leakage")
    finally:
        token.reset()

    assert catalog.categories[0].name == "机密性"
    assert catalog.categories[0].subcategories[0].name == "身份泄露"
    assert catalog.categories[0].subcategories[0].short_description == "短描述"
    assert detail.full_description == "完整描述"
    assert detail.highlights == ["亮点"]
    assert detail.scenarios == ["场景"]
    assert detail.resources[0]["label"] == "文档"
    assert detail.media[0]["title"] == "示意图"


class SampleProfileRepositoryStub(DatasetRepositoryStub):
    async def get_detail_sample_rows(self, dataset_id: str):
        return [
            SimpleNamespace(
                delivery_code="popup_on_webpage",
                delivery_name="网页弹窗或覆盖层",
                asset_type_code=None,
                asset_type_name=None,
                difficulty_score=Decimal("0.750"),
            ),
            SimpleNamespace(
                delivery_code="injected_text_on_webpage",
                delivery_name="网页注入文本",
                asset_type_code="credential",
                asset_type_name="凭证",
                difficulty_score=Decimal("0.500"),
            ),
            SimpleNamespace(
                delivery_code="popup_on_webpage",
                delivery_name="网页弹窗或覆盖层",
                asset_type_code=None,
                asset_type_name=None,
                difficulty_score=Decimal("0.250"),
            ),
            *[
                SimpleNamespace(
                    delivery_code="popup_on_webpage",
                    delivery_name="网页弹窗或覆盖层",
                    asset_type_code=f"asset_{index}",
                    asset_type_name=f"资产 {index}",
                    difficulty_score=Decimal("0.100"),
                )
                for index in range(1, 7)
            ],
        ]


@pytest.mark.asyncio
async def test_dataset_detail_includes_sample_profile_aggregates() -> None:
    now = datetime.now(timezone.utc)
    category = SimpleNamespace(
        id=1,
        code="unauthorized_execution_and_system_control",
        name="未授权执行与系统控制",
        meaning="代理不得执行未授权命令。",
        description="系统控制风险。",
        sort_order=4,
        is_active=True,
        updated_at=now,
    )
    subtype = SimpleNamespace(
        id=2, code="D1_command_execution", name="命令执行", is_active=True, sort_order=1
    )
    display_meta = SimpleNamespace(
        subtype_id=2,
        short_description="评估命令执行风险。",
        full_description="完整说明",
        highlights=[],
        scenarios=[],
        resources=[],
        media=[],
        updated_at=now,
    )
    service = DatasetService(SampleProfileRepositoryStub(category, subtype, display_meta))

    detail = await service.get_detail("D1_command_execution")

    assert [
        (item.code, item.label, item.count)
        for item in detail.sample_profile.delivery_distribution
    ] == [
        ("popup_on_webpage", "网页弹窗或覆盖层", 8),
        ("injected_text_on_webpage", "网页注入文本", 1),
    ]
    assert [
        (item.code, item.label, item.count)
        for item in detail.sample_profile.asset_type_top
    ] == [
        ("__unassigned__", "未标记资产", 2),
        ("credential", "凭证", 1),
        ("asset_1", "资产 1", 1),
        ("asset_2", "资产 2", 1),
        ("asset_3", "资产 3", 1),
    ]
    assert set(detail.sample_profile.model_dump()) == {
        "asset_type_top",
        "delivery_distribution",
        "difficulty_buckets",
    }
    assert [
        (item.code, item.count) for item in detail.sample_profile.difficulty_buckets
    ] == [
        ("0.0-0.2", 6),
        ("0.2-0.4", 1),
        ("0.4-0.6", 1),
        ("0.6-0.8", 1),
        ("0.8-1.0", 0),
    ]


class LocalizedSampleProfileRepositoryStub(DatasetRepositoryStub):
    async def get_detail_sample_rows(self, dataset_id: str):
        return [
            SimpleNamespace(
                delivery_code="popup_on_webpage",
                delivery_name="网页弹窗或覆盖层",
                delivery_translations={
                    "fr-FR": {"name": "Fenêtre contextuelle ou superposition Web"}
                },
                asset_type_code=None,
                asset_type_name=None,
                asset_type_translations=None,
                difficulty_score=Decimal("0.750"),
            ),
            SimpleNamespace(
                delivery_code="injected_text_on_webpage",
                delivery_name="网页注入文本",
                delivery_translations={
                    "fr-FR": {"name": "Texte injecté dans la page Web"}
                },
                asset_type_code="credential",
                asset_type_name="凭证",
                asset_type_translations={"fr-FR": {"name": "Identifiants"}},
                difficulty_score=Decimal("0.500"),
            ),
        ]


@pytest.mark.asyncio
async def test_dataset_detail_localizes_sample_profile_dictionary_labels() -> None:
    now = datetime.now(timezone.utc)
    category = SimpleNamespace(
        id=1,
        code="unauthorized_execution_and_system_control",
        name="未授权执行与系统控制",
        meaning="代理不得执行未授权命令。",
        description="系统控制风险。",
        sort_order=4,
        is_active=True,
        updated_at=now,
    )
    subtype = SimpleNamespace(
        id=2, code="D1_command_execution", name="命令执行", is_active=True, sort_order=1
    )
    display_meta = SimpleNamespace(
        subtype_id=2,
        short_description="评估命令执行风险。",
        full_description="完整说明",
        highlights=[],
        scenarios=[],
        resources=[],
        media=[],
        updated_at=now,
    )
    token = set_current_locale("fr-FR")
    try:
        service = DatasetService(
            LocalizedSampleProfileRepositoryStub(category, subtype, display_meta)
        )
        detail = await service.get_detail("D1_command_execution")
    finally:
        token.reset()

    assert [
        (item.code, item.label, item.count)
        for item in detail.sample_profile.delivery_distribution
    ] == [
        ("popup_on_webpage", "Fenêtre contextuelle ou superposition Web", 1),
        ("injected_text_on_webpage", "Texte injecté dans la page Web", 1),
    ]
    assert [
        (item.code, item.label, item.count)
        for item in detail.sample_profile.asset_type_top
    ] == [
        ("__unassigned__", "Actif non renseigné", 1),
        ("credential", "Identifiants", 1),
    ]
