"""数据集模块请求与响应模型。"""

from app.platform.schemas import CamelModel


class EvaluationItemCatalogItem(CamelModel):
    """目录中单个评测项的摘要信息。"""

    evaluation_item_id: str
    name: str
    short_description: str | None = None
    sample_count: int
    updated_at: str
    enabled: bool


class RiskDomainCatalogItem(CamelModel):
    """目录中的风险域分组。"""

    risk_domain_id: str
    name: str
    meaning: str | None = None
    description: str | None = None
    sort: int | None = None
    enabled: bool
    evaluation_item_count: int
    sample_count: int
    evaluation_items: list[EvaluationItemCatalogItem]


class AttackScenarioCatalogItem(CamelModel):
    """目录中的攻击场景分组。"""

    attack_scenario_id: str
    name: str
    description: str | None = None
    sort: int | None = None
    enabled: bool
    risk_domain_count: int
    evaluation_item_count: int
    sample_count: int
    risk_domains: list[RiskDomainCatalogItem]


class DatasetCatalogResponse(CamelModel):
    """攻击场景库目录接口响应体。"""

    catalog_version: str
    attack_scenario_count: int
    risk_domain_count: int
    evaluation_item_count: int
    attack_scenarios: list[AttackScenarioCatalogItem]


class AttackScenarioInfo(CamelModel):
    """评测项详情中的攻击场景信息。"""

    attack_scenario_id: str
    name: str
    description: str | None = None


class RiskDomainInfo(CamelModel):
    """评测项详情中的风险域信息。"""

    risk_domain_id: str
    name: str
    meaning: str | None = None


class DatasetDistributionItem(CamelModel):
    """数据集详情聚合分布中的单个条目。"""

    code: str
    label: str
    count: int
    ratio: float


class DatasetSampleProfile(CamelModel):
    """数据集详情页使用的样本级聚合摘要。"""

    delivery_distribution: list[DatasetDistributionItem]
    asset_type_top: list[DatasetDistributionItem]
    difficulty_buckets: list[DatasetDistributionItem]


class DatasetDetailResponse(CamelModel):
    """评测项详情接口响应体。"""

    evaluation_item_id: str
    name: str
    attack_scenario: AttackScenarioInfo
    risk_domain: RiskDomainInfo
    short_description: str | None = None
    full_description: str | None = None
    sample_count: int
    updated_at: str
    highlights: list[str]
    scenarios: list[str]
    resources: list[dict[str, object]]
    media: list[dict[str, object]]
    sample_profile: DatasetSampleProfile
