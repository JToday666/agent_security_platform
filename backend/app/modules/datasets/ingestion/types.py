"""数据集导入链路的共享类型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Literal


@dataclass(slots=True)
class PlannedOracle:
    """描述单条待导入的判定规则。"""

    oracle_kind: int
    seq_no: int
    display_text: str
    evaluator_type: str = "manual_review"
    evaluator_config: dict[str, object] = field(default_factory=dict)
    is_active: bool = True


@dataclass(slots=True)
class PlannedSample:
    """描述单个待导入样本的标准化结果。"""

    sample_id: str
    sample_name: str
    resource_path: str
    entry_path: str
    dataset_source_code: str
    dataset_source_name: str
    attack_delivery_type_code: str
    attack_delivery_type_name: str
    risk_category_code: str
    risk_category_name: str
    risk_category_sort_order: int | None
    risk_subtype_code: str
    risk_subtype_name: str
    risk_subtype_sort_order: int | None
    asset_type_code: str | None
    asset_type_name: str | None
    user_goal: str
    attacker_goal: str | None
    attacker_is_user: bool
    risk_level: int
    attack_level: int
    difficulty_seed: Decimal
    difficulty_score: Decimal
    expected_safe_behavior: str
    metadata_path: Path
    oracles: list[PlannedOracle]
    is_active: bool = True


@dataclass(slots=True)
class SampleImportPlan:
    """汇总一次样本导入所需的标准化样本集合。"""

    sample_root: Path
    samples: list[PlannedSample]


ImportPlan = SampleImportPlan


@dataclass(slots=True)
class SampleImportResult:
    """记录样本导入执行后的新增与更新统计。"""

    created_samples: int = 0
    updated_samples: int = 0
    created_oracles: int = 0
    updated_oracles: int = 0
    deactivated_oracles: int = 0


ImportResult = SampleImportResult


@dataclass(slots=True)
class DatasetSourceRecord:
    """描述 registry 中的数据源字典项。"""

    code: str
    name: str
    description: str | None = None
    is_active: bool = True
    translations: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass(slots=True)
class AttackDeliveryTypeRecord:
    """描述 registry 中的攻击投递方式字典项。"""

    code: str
    name: str
    description: str | None = None
    is_active: bool = True
    translations: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass(slots=True)
class AssetTypeRecord:
    """描述 registry 中的资产类型字典项。"""

    code: str
    name: str
    description: str | None = None
    is_active: bool = True
    translations: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass(slots=True)
class RiskCategoryRecord:
    """描述 registry 中的风险大类字典项。"""

    code: str
    name: str
    meaning: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool = True
    translations: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass(slots=True)
class RiskSubtypeRecord:
    """描述 registry 中的风险子类字典项。"""

    code: str
    category_code: str
    name: str
    sort_order: int | None = None
    is_active: bool = True
    translations: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass(slots=True)
class DisplayMetaRecord:
    """描述展示层使用的风险子类富文本资料。"""

    subtype_code: str
    short_description: str | None = None
    full_description: str | None = None
    highlights: list[str] = field(default_factory=list)
    scenarios: list[str] = field(default_factory=list)
    resources: list[dict[str, object]] = field(default_factory=list)
    media: list[dict[str, object]] = field(default_factory=list)
    translations: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass(slots=True)
class MetadataBundle:
    """汇总一套可读写的版本化元数据内容。"""

    dataset_sources: list[DatasetSourceRecord] = field(default_factory=list)
    attack_delivery_types: list[AttackDeliveryTypeRecord] = field(default_factory=list)
    asset_types: list[AssetTypeRecord] = field(default_factory=list)
    risk_categories: list[RiskCategoryRecord] = field(default_factory=list)
    risk_subtypes: list[RiskSubtypeRecord] = field(default_factory=list)
    display_meta_by_code: dict[str, DisplayMetaRecord] = field(default_factory=dict)


@dataclass(slots=True)
class MetadataImportResult:
    """记录元数据入库后的新增与更新统计。"""

    created_sources: int = 0
    updated_sources: int = 0
    created_delivery_types: int = 0
    updated_delivery_types: int = 0
    created_asset_types: int = 0
    updated_asset_types: int = 0
    created_categories: int = 0
    updated_categories: int = 0
    created_subtypes: int = 0
    updated_subtypes: int = 0
    created_display_meta: int = 0
    updated_display_meta: int = 0


@dataclass(slots=True)
class NormalizationResult:
    """记录一次标准化执行的统计结果。"""

    input_root: Path
    output_root: Path
    sample_count: int = 0
    written_task_count: int = 0
    symlinked_file_count: int = 0


@dataclass(slots=True)
class ImportPipelineResult:
    """记录顶层导入 pipeline 的执行摘要。"""

    input_kind: Literal["raw", "standard"]
    sample_root: Path
    effective_sample_root: Path
    registry_root: Path
    sample_plan: SampleImportPlan
    metadata_bundle: MetadataBundle
    normalized: bool = False
    normalization_result: NormalizationResult | None = None
    metadata_result: MetadataImportResult | None = None
    sample_result: SampleImportResult | None = None

    @property
    def sample_count(self) -> int:
        """返回 pipeline 最终参与导入的样本数。"""
        return len(self.sample_plan.samples)
