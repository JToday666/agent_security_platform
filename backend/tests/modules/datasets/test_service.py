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
        scenario,
        category,
        subtype,
        display_meta,
        sample_count: int,
        sample_updated_at: datetime,
    ) -> None:
        self.scenario = scenario
        self.category = category
        self.subtype = subtype
        self.display_meta = display_meta
        self.sample_count = sample_count
        self.sample_updated_at = sample_updated_at

    def __iter__(self):
        yield self.scenario
        yield self.category
        yield self.subtype
        yield self.display_meta
        yield self.sample_count
        yield self.sample_updated_at


class DatasetRepositoryStub:
    def __init__(self, category, subtype, display_meta) -> None:
        self.scenario = SimpleNamespace(
            id=10,
            code="prompt_injection",
            name="提示注入",
            description="覆盖提示注入攻击。",
            sort_order=1,
            is_active=True,
            updated_at=display_meta.updated_at,
        )
        self.category = category
        self.subtype = subtype
        self.display_meta = display_meta

    async def get_catalog_rows(self):
        return [
            DatasetRow(
                self.scenario,
                self.category,
                self.subtype,
                self.display_meta,
                3,
                self.display_meta.updated_at,
            )
        ]

    async def get_detail_row(self, dataset_id: str):
        return DatasetRow(
            self.scenario,
            self.category,
            self.subtype,
            self.display_meta,
            3,
            self.display_meta.updated_at,
        )

    async def get_detail_sample_rows(self, dataset_id: str):
        return []

    async def load_translation_maps(
        self,
        locale: str,
        scenario_ids: list[int],
        category_ids: list[int],
        subtype_ids: list[int],
    ):
        return {
            "scenarios": {
                10: {
                    "name": "Prompt Injection",
                    "description": "Indirect and direct prompt injection attacks.",
                }
            },
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
        self,
        locale: str,
        scenario_ids: list[int],
        category_ids: list[int],
        subtype_ids: list[int],
    ):
        return {
            "scenarios": {
                10: {
                    "name": "",
                    "description": "",
                }
            },
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

    def one_or_none(self):
        return self.rows[0] if self.rows else None

    def mappings(self):
        return self


class TranslationSessionStub:
    def __init__(self) -> None:
        self.results = [
            [(10, {"en-US": {"name": "Prompt Injection"}})],
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


class CaptureExecuteSession:
    def __init__(self) -> None:
        self.statements = []

    async def execute(self, stmt):
        self.statements.append(stmt)
        return ExecuteRows([])


@pytest.mark.asyncio
async def test_dataset_repository_public_queries_exclude_internal_fixture_codes() -> None:
    session = CaptureExecuteSession()
    repository = DatasetRepository(session)

    await repository.get_catalog_rows()
    await repository.get_detail_row("pytest_abcd_dataset")
    await repository.get_detail_sample_rows("pytest_abcd_dataset")

    compiled_params = [
        value
        for statement in session.statements
        for value in statement.compile().params.values()
    ]
    assert compiled_params.count("pytest_%") == 3


@pytest.mark.asyncio
async def test_dataset_repository_loads_locale_translation_maps() -> None:
    repository = DatasetRepository(TranslationSessionStub())

    assert await repository.load_translation_maps("en-US", [10], [1], [2]) == {
        "scenarios": {10: {"name": "Prompt Injection"}},
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

    prompt = catalog.attack_scenarios[0]
    risk_domain = prompt.risk_domains[0]
    evaluation_item = risk_domain.evaluation_items[0]
    assert prompt.name == "Prompt Injection"
    assert risk_domain.name == "Confidentiality"
    assert risk_domain.meaning == "Protect sensitive information."
    assert (
        risk_domain.description
        == "Risks related to sensitive information exposure."
    )
    assert evaluation_item.name == "Identity Leakage"
    assert evaluation_item.short_description == "Short English description."
    assert detail.name == "Identity Leakage"
    assert detail.attack_scenario.name == "Prompt Injection"
    assert detail.risk_domain.name == "Confidentiality"
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

    risk_domain = catalog.attack_scenarios[0].risk_domains[0]
    evaluation_item = risk_domain.evaluation_items[0]
    assert catalog.attack_scenarios[0].name == "提示注入"
    assert risk_domain.name == "机密性"
    assert evaluation_item.name == "身份泄露"
    assert evaluation_item.short_description == "短描述"
    assert detail.full_description == "完整描述"
    assert detail.highlights == ["亮点"]
    assert detail.scenarios == ["场景"]
    assert detail.resources[0]["label"] == "文档"
    assert detail.media[0]["title"] == "示意图"


class AttackScenarioRepositoryStub(DatasetRepositoryStub):
    async def get_attack_scenario_rows(self):
        now = self.display_meta.updated_at
        return [
            SimpleNamespace(
                id=10,
                code="prompt_injection",
                name="提示注入",
                description="覆盖提示注入攻击。",
                sort_order=1,
                is_active=True,
                updated_at=now,
            ),
            SimpleNamespace(
                id=11,
                code="model_abuse_and_unauthorized_actions",
                name="模型滥用与越权行为",
                description="覆盖模型滥用与越权操作。",
                sort_order=2,
                is_active=True,
                updated_at=now,
            ),
        ]

    async def get_catalog_rows(self):
        now = self.display_meta.updated_at
        prompt = SimpleNamespace(
            id=10,
            code="prompt_injection",
            name="提示注入",
            description="覆盖提示注入攻击。",
            sort_order=1,
            is_active=True,
            updated_at=now,
        )
        abuse = SimpleNamespace(
            id=11,
            code="model_abuse_and_unauthorized_actions",
            name="模型滥用与越权行为",
            description="覆盖模型滥用与越权操作。",
            sort_order=2,
            is_active=True,
            updated_at=now,
        )
        confidentiality = SimpleNamespace(
            id=1,
            code="confidentiality",
            name="机密性",
            meaning="保护敏感信息。",
            description="敏感信息暴露相关风险。",
            sort_order=1,
            is_active=True,
            updated_at=now,
            risk_domain_sort_order=1,
        )
        execution = SimpleNamespace(
            id=3,
            code="unauthorized_execution_and_system_control",
            name="未授权执行与系统控制",
            meaning="代理不得执行未授权命令。",
            description="系统控制风险。",
            sort_order=4,
            is_active=True,
            updated_at=now,
            risk_domain_sort_order=1,
        )
        d1 = SimpleNamespace(
            id=4,
            code="D1_command_execution",
            name="命令执行",
            is_active=True,
            sort_order=1,
        )
        return [
            DatasetRow(prompt, confidentiality, self.subtype, self.display_meta, 3, now),
            DatasetRow(abuse, execution, d1, self.display_meta, 2, now),
        ]

    async def get_detail_row(self, dataset_id: str):
        scenario = SimpleNamespace(
            id=10,
            code="prompt_injection",
            name="提示注入",
            description="覆盖提示注入攻击。",
            sort_order=1,
            is_active=True,
            updated_at=self.display_meta.updated_at,
        )
        return DatasetRow(
            scenario,
            self.category,
            self.subtype,
            self.display_meta,
            3,
            self.display_meta.updated_at,
        )

    async def load_translation_maps(
        self,
        locale: str,
        scenario_ids: list[int],
        category_ids: list[int],
        subtype_ids: list[int],
    ):
        return {
            "scenarios": {},
            "categories": {},
            "subtypes": {},
            "display_meta": {},
        }


@pytest.mark.asyncio
async def test_attack_scenario_catalog_groups_risk_domains_and_evaluation_items() -> None:
    now = datetime.now(timezone.utc)
    category = SimpleNamespace(
        id=1,
        code="confidentiality",
        name="机密性",
        meaning="保护敏感信息。",
        description="敏感信息暴露相关风险。",
        sort_order=1,
        risk_domain_sort_order=1,
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
        highlights=[],
        scenarios=[],
        resources=[],
        media=[],
        updated_at=now,
    )
    service = DatasetService(
        AttackScenarioRepositoryStub(category, subtype, display_meta)
    )

    catalog = await service.get_catalog()

    assert [scenario.attack_scenario_id for scenario in catalog.attack_scenarios] == [
        "prompt_injection",
        "model_abuse_and_unauthorized_actions",
    ]
    prompt = catalog.attack_scenarios[0]
    assert prompt.risk_domains[0].risk_domain_id == "confidentiality"
    assert prompt.risk_domains[0].evaluation_items[0].evaluation_item_id == (
        "A1_identity_leakage"
    )
    assert catalog.attack_scenario_count == 2
    assert catalog.risk_domain_count == 2
    assert catalog.evaluation_item_count == 2


@pytest.mark.asyncio
async def test_evaluation_item_detail_includes_attack_scenario_and_risk_domain() -> None:
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
        resources=[],
        media=[],
        updated_at=now,
    )
    service = DatasetService(
        AttackScenarioRepositoryStub(category, subtype, display_meta)
    )

    detail = await service.get_detail("A1_identity_leakage")

    assert detail.evaluation_item_id == "A1_identity_leakage"
    assert detail.attack_scenario.attack_scenario_id == "prompt_injection"
    assert detail.risk_domain.risk_domain_id == "confidentiality"


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


class EmptyAttackScenarioRepositoryStub(AttackScenarioRepositoryStub):
    async def get_catalog_rows(self):
        rows = await super().get_catalog_rows()
        now = self.display_meta.updated_at
        poisoning = SimpleNamespace(
            id=12,
            code="knowledge_base_poisoning",
            name="知识库投毒",
            description="覆盖知识库污染与检索误导。",
            sort_order=3,
            is_active=True,
            updated_at=now,
        )
        knowledge_integrity = SimpleNamespace(
            id=12,
            code="knowledge_base_integrity",
            name="知识库完整性",
            meaning="保护知识库内容不被污染。",
            description="知识库污染相关风险。",
            sort_order=1,
            is_active=True,
            updated_at=now,
            risk_domain_sort_order=1,
        )
        poisoned_retrieval = SimpleNamespace(
            id=13,
            code="K1_poisoned_retrieval",
            name="检索内容投毒",
            is_active=True,
            sort_order=1,
        )
        return [
            *rows,
            DatasetRow(
                poisoning,
                knowledge_integrity,
                poisoned_retrieval,
                self.display_meta,
                0,
                None,
            ),
        ]

    async def get_attack_scenario_rows(self):
        now = self.display_meta.updated_at
        return [
            *(await super().get_attack_scenario_rows()),
            SimpleNamespace(
                id=12,
                code="knowledge_base_poisoning",
                name="知识库投毒",
                description="覆盖知识库污染与检索误导。",
                sort_order=3,
                is_active=True,
                updated_at=now,
            ),
            SimpleNamespace(
                id=13,
                code="tool_call_hijacking",
                name="工具调用劫持",
                description="覆盖工具调用参数和流程劫持。",
                sort_order=4,
                is_active=True,
                updated_at=now,
            ),
        ]

    async def load_translation_maps(
        self,
        locale: str,
        scenario_ids: list[int],
        category_ids: list[int],
        subtype_ids: list[int],
    ):
        _ = locale, category_ids, subtype_ids
        return {
            "scenarios": {
                scenario_id: {"name": name}
                for scenario_id, name in {
                    10: "Prompt Injection",
                    11: "Model Abuse and Unauthorized Actions",
                    12: "Knowledge Base Poisoning",
                    13: "Tool Call Hijacking",
                }.items()
                if scenario_id in scenario_ids
            },
            "categories": {},
            "subtypes": {},
            "display_meta": {},
        }


@pytest.mark.asyncio
async def test_attack_scenario_catalog_includes_empty_active_scenarios() -> None:
    now = datetime.now(timezone.utc)
    category = SimpleNamespace(
        id=1,
        code="confidentiality",
        name="机密性",
        meaning="保护敏感信息。",
        description="敏感信息暴露相关风险。",
        sort_order=1,
        risk_domain_sort_order=1,
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
        highlights=[],
        scenarios=[],
        resources=[],
        media=[],
        updated_at=now,
    )
    token = set_current_locale("en-US")
    try:
        service = DatasetService(
            EmptyAttackScenarioRepositoryStub(category, subtype, display_meta)
        )
        catalog = await service.get_catalog()
    finally:
        token.reset()

    assert [scenario.attack_scenario_id for scenario in catalog.attack_scenarios] == [
        "prompt_injection",
        "model_abuse_and_unauthorized_actions",
        "knowledge_base_poisoning",
        "tool_call_hijacking",
    ]
    assert catalog.attack_scenario_count == 4
    assert catalog.attack_scenarios[2].name == "Knowledge Base Poisoning"
    assert catalog.attack_scenarios[2].risk_domain_count == 0
    assert catalog.attack_scenarios[2].evaluation_item_count == 0
    assert catalog.attack_scenarios[2].sample_count == 0
    assert catalog.attack_scenarios[2].risk_domains == []


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
