"""datasets_demo 旧格式样本导入逻辑。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benchmark import (
    AssetType,
    AttackDeliveryType,
    BenchmarkSample,
    DatasetSource,
    RiskCategory,
    RiskSubtype,
    SampleOracle,
)


IGNORED_JSON_FILENAMES = {"package.json", "package-lock.json", "default.json"}
LEGACY_REQUIRED_KEYS = {
    "sample_id",
    "dataset_source",
    "attack_delivery",
    "primary_risk",
    "secondary_risk",
    "risk_level",
    "attack_level",
    "expected_safe_behavior",
    "success_oracle",
    "harm_oracle",
}
LEVEL_CODE_TO_VALUE = {"low": 1, "medium": 2, "high": 3}
DATASET_SOURCE_CODE_ALIASES = {
    "EIA": "eia",
    "VPI-bench": "vpi_bench",
    "BrowserART": "browser_art",
    "browser-art": "browser_art",
}
CATEGORY_DEFINITIONS = {
    "01_Confidentiality": {"code": "confidentiality", "name": "Confidentiality", "sort_order": 1},
    "02_Integrity": {"code": "integrity", "name": "Integrity", "sort_order": 2},
}
SUBTYPE_DEFINITIONS = {
    "A1_Identity_Information_Leakage": {
        "code": "A1_identity_leakage",
        "name": "Identity Leakage",
        "sort_order": 1,
    },
    "A5_Credentials_and_Secrets_Leakage": {
        "code": "A5_credentials_and_secrets_leakage",
        "name": "Credentials and Secrets Leakage",
        "sort_order": 5,
    },
    "B2_Cloud_File_Modification": {
        "code": "B2_cloud_file_modification",
        "name": "Cloud File Modification",
        "sort_order": 2,
    },
    "B5_Identity_Forgery_Modification": {
        "code": "B5_identity_forgery_modification",
        "name": "Identity Forgery Modification",
        "sort_order": 5,
    },
}


class ImportValidationError(ValueError):
    """导入输入不合法。"""


@dataclass(slots=True)
class PlannedOracle:
    oracle_kind: int
    seq_no: int
    display_text: str
    evaluator_type: str = "manual_review"
    evaluator_config: dict[str, object] = field(default_factory=dict)
    is_active: bool = True


@dataclass(slots=True)
class PlannedSample:
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
    risk_category_sort_order: int
    risk_subtype_code: str
    risk_subtype_name: str
    risk_subtype_sort_order: int
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
class ImportPlan:
    sample_root: Path
    samples: list[PlannedSample]


@dataclass(slots=True)
class ImportResult:
    created_sources: int = 0
    updated_sources: int = 0
    created_delivery_types: int = 0
    updated_delivery_types: int = 0
    created_categories: int = 0
    updated_categories: int = 0
    created_subtypes: int = 0
    updated_subtypes: int = 0
    created_asset_types: int = 0
    updated_asset_types: int = 0
    created_samples: int = 0
    updated_samples: int = 0
    created_oracles: int = 0
    updated_oracles: int = 0


def discover_legacy_sample_files(sample_root: Path) -> list[Path]:
    """返回 demo 目录中可导入的旧格式样本 JSON。"""
    root = sample_root.resolve()
    if not root.exists():
        raise ImportValidationError(f"样本根目录不存在: {root}")

    sample_files: list[Path] = []
    for path in sorted(root.rglob("*.json")):
        if path.name in IGNORED_JSON_FILENAMES or "saved_logs" in path.parts:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ImportValidationError(f"JSON 解析失败: {path}: {exc}") from exc
        if isinstance(payload, dict) and LEGACY_REQUIRED_KEYS.issubset(payload):
            sample_files.append(path)

    return sample_files


def build_import_plan(sample_root: Path) -> ImportPlan:
    """扫描并标准化旧格式样本目录。"""
    root = sample_root.resolve()
    sample_files = discover_legacy_sample_files(root)
    if not sample_files:
        raise ImportValidationError(f"未在 {root} 下发现可导入的旧格式样本")

    samples = [_normalize_sample(metadata_path, root) for metadata_path in sample_files]
    samples.sort(key=lambda item: (item.dataset_source_code, item.sample_id))
    return ImportPlan(sample_root=root, samples=samples)


def compute_difficulty_seed(risk_level: int, attack_level: int) -> Decimal:
    """按附录公式计算初始难度。"""
    risk_norm = Decimal(risk_level - 1) / Decimal(2)
    attack_norm = Decimal(attack_level - 1) / Decimal(2)
    difficulty = Decimal("0.35") * risk_norm + Decimal("0.65") * attack_norm
    difficulty = max(Decimal("0"), min(Decimal("1"), difficulty))
    return difficulty.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def apply_import_plan(session: Session, plan: ImportPlan) -> ImportResult:
    """将导入计划写入数据库。调用方负责提交事务。"""
    result = ImportResult()

    source_cache: dict[str, DatasetSource] = {}
    delivery_cache: dict[str, AttackDeliveryType] = {}
    category_cache: dict[str, RiskCategory] = {}
    subtype_cache: dict[str, RiskSubtype] = {}
    asset_cache: dict[str, AssetType] = {}

    for sample in plan.samples:
        source = source_cache.get(sample.dataset_source_code)
        if source is None:
            source, created = _upsert_dataset_source(
                session,
                code=sample.dataset_source_code,
                name=sample.dataset_source_name,
            )
            source_cache[sample.dataset_source_code] = source
            if created:
                result.created_sources += 1
            else:
                result.updated_sources += 1

        delivery = delivery_cache.get(sample.attack_delivery_type_code)
        if delivery is None:
            delivery, created = _upsert_attack_delivery_type(
                session,
                code=sample.attack_delivery_type_code,
                name=sample.attack_delivery_type_name,
            )
            delivery_cache[sample.attack_delivery_type_code] = delivery
            if created:
                result.created_delivery_types += 1
            else:
                result.updated_delivery_types += 1

        category = category_cache.get(sample.risk_category_code)
        if category is None:
            category, created = _upsert_risk_category(
                session,
                code=sample.risk_category_code,
                name=sample.risk_category_name,
                sort_order=sample.risk_category_sort_order,
            )
            category_cache[sample.risk_category_code] = category
            if created:
                result.created_categories += 1
            else:
                result.updated_categories += 1

        subtype = subtype_cache.get(sample.risk_subtype_code)
        if subtype is None:
            subtype, created = _upsert_risk_subtype(
                session,
                category_id=category.id,
                code=sample.risk_subtype_code,
                name=sample.risk_subtype_name,
                sort_order=sample.risk_subtype_sort_order,
            )
            subtype_cache[sample.risk_subtype_code] = subtype
            if created:
                result.created_subtypes += 1
            else:
                result.updated_subtypes += 1

        asset = None
        if sample.asset_type_code and sample.asset_type_name:
            asset = asset_cache.get(sample.asset_type_code)
            if asset is None:
                asset, created = _upsert_asset_type(
                    session,
                    code=sample.asset_type_code,
                    name=sample.asset_type_name,
                )
                asset_cache[sample.asset_type_code] = asset
                if created:
                    result.created_asset_types += 1
                else:
                    result.updated_asset_types += 1

        sample_row, created = _upsert_benchmark_sample(
            session,
            dataset_source_id=source.id,
            sample=sample,
            attack_delivery_type_id=delivery.id,
            risk_subtype_id=subtype.id,
            asset_type_id=asset.id if asset is not None else None,
        )
        if created:
            result.created_samples += 1
        else:
            result.updated_samples += 1

        for oracle in sample.oracles:
            _, created = _upsert_sample_oracle(session, sample_row.id, oracle)
            if created:
                result.created_oracles += 1
            else:
                result.updated_oracles += 1

    session.flush()
    return result


def _normalize_sample(metadata_path: Path, sample_root: Path) -> PlannedSample:
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    sample_dir = metadata_path.parent

    sample_id = _require_non_empty_text(payload.get("sample_id"), metadata_path, "sample_id")
    dataset_source_name = _require_non_empty_text(payload.get("dataset_source"), metadata_path, "dataset_source")
    attack_delivery_name = _require_non_empty_text(payload.get("attack_delivery"), metadata_path, "attack_delivery")
    primary_risk = _require_non_empty_text(payload.get("primary_risk"), metadata_path, "primary_risk")
    secondary_risk = _require_non_empty_text(payload.get("secondary_risk"), metadata_path, "secondary_risk")
    user_goal = _require_non_empty_text(payload.get("user_goal"), metadata_path, "user_goal")
    expected_safe_behavior = _require_non_empty_text(
        payload.get("expected_safe_behavior"),
        metadata_path,
        "expected_safe_behavior",
    )
    if not isinstance(payload.get("attacker_is_user"), bool):
        raise ImportValidationError(f"{metadata_path}: attacker_is_user 必须是布尔值")

    category_definition = CATEGORY_DEFINITIONS.get(primary_risk)
    if category_definition is None:
        raise ImportValidationError(f"{metadata_path}: 不支持的 primary_risk={primary_risk}")

    subtype_definition = SUBTYPE_DEFINITIONS.get(secondary_risk)
    if subtype_definition is None:
        raise ImportValidationError(f"{metadata_path}: 不支持的 secondary_risk={secondary_risk}")

    risk_level = _normalize_level(payload.get("risk_level"), metadata_path, "risk_level")
    attack_level = _normalize_level(payload.get("attack_level"), metadata_path, "attack_level")
    difficulty_seed = compute_difficulty_seed(risk_level, attack_level)
    entry_path = _resolve_entry_path(payload, sample_dir, metadata_path)
    resource_path = sample_dir.relative_to(sample_root).as_posix()

    asset_type_name = _optional_text(payload.get("asset_type"))
    asset_type_code = normalize_code(asset_type_name) if asset_type_name else None

    return PlannedSample(
        sample_id=sample_id,
        sample_name=_optional_text(payload.get("sample_name")) or sample_id,
        resource_path=resource_path,
        entry_path=entry_path,
        dataset_source_code=_normalize_dataset_source_code(dataset_source_name),
        dataset_source_name=dataset_source_name,
        attack_delivery_type_code=normalize_code(attack_delivery_name),
        attack_delivery_type_name=attack_delivery_name,
        risk_category_code=category_definition["code"],
        risk_category_name=category_definition["name"],
        risk_category_sort_order=category_definition["sort_order"],
        risk_subtype_code=subtype_definition["code"],
        risk_subtype_name=subtype_definition["name"],
        risk_subtype_sort_order=subtype_definition["sort_order"],
        asset_type_code=asset_type_code,
        asset_type_name=asset_type_name,
        user_goal=user_goal,
        attacker_goal=_optional_text(payload.get("attacker_goal")),
        attacker_is_user=payload["attacker_is_user"],
        risk_level=risk_level,
        attack_level=attack_level,
        difficulty_seed=difficulty_seed,
        difficulty_score=difficulty_seed,
        expected_safe_behavior=expected_safe_behavior,
        metadata_path=metadata_path,
        oracles=_normalize_oracles(payload, metadata_path),
    )


def _normalize_oracles(payload: dict[str, object], metadata_path: Path) -> list[PlannedOracle]:
    oracles: list[PlannedOracle] = []
    for oracle_kind, field_name in ((1, "success_oracle"), (2, "harm_oracle")):
        raw_list = payload.get(field_name)
        if not isinstance(raw_list, list) or not raw_list:
            raise ImportValidationError(f"{metadata_path}: {field_name} 必须是非空数组")
        for index, item in enumerate(raw_list, start=1):
            text = _optional_text(item)
            if not text:
                raise ImportValidationError(f"{metadata_path}: {field_name}[{index}] 必须是非空字符串")
            oracles.append(PlannedOracle(oracle_kind=oracle_kind, seq_no=index, display_text=text))
    return oracles


def _resolve_entry_path(payload: dict[str, object], sample_dir: Path, metadata_path: Path) -> str:
    entry_url = _optional_text(payload.get("entry_url"))
    if entry_url:
        direct_candidate = _coerce_relative_entry_candidate(entry_url)
        if direct_candidate and (sample_dir / direct_candidate).is_file():
            return direct_candidate

    for field_name in ("user_goal", "attacker_goal"):
        text = _optional_text(payload.get(field_name))
        if not text:
            continue
        for candidate in _extract_goal_entry_candidates(text):
            if (sample_dir / candidate).is_file():
                return candidate

    adv_html = sorted(path.name for path in sample_dir.glob("adv_*.html") if path.is_file())
    if len(adv_html) == 1:
        return adv_html[0]

    index_files = sorted(
        path.relative_to(sample_dir).as_posix()
        for path in sample_dir.rglob("index.html")
        if path.is_file()
    )
    if len(index_files) == 1:
        return index_files[0]

    raise ImportValidationError(f"{metadata_path}: 无法确定 entry_path")


def _extract_goal_entry_candidates(text: str) -> list[str]:
    quoted_segments = re.findall(r"""['"]([^'"]+?\.html(?:[^'"]*)?)['"]""", text)
    candidates: list[str] = []
    for segment in quoted_segments:
        candidate = _coerce_relative_entry_candidate(segment)
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _coerce_relative_entry_candidate(raw_value: str) -> str | None:
    value = raw_value.strip()
    if not value:
        return None

    if "://" in value:
        parsed = urlparse(value)
        value = parsed.path

    value = value.strip()
    if not value:
        return None

    value = value.lstrip("/")
    value = value.replace("\\", "/")
    if not value.endswith(".html"):
        return None
    if Path(value).is_absolute():
        return None
    if ".." in Path(value).parts:
        return None
    return value


def _normalize_level(value: object, metadata_path: Path, field_name: str) -> int:
    normalized = _optional_text(value)
    level = LEVEL_CODE_TO_VALUE.get(normalized or "")
    if level is None:
        raise ImportValidationError(f"{metadata_path}: {field_name} 仅支持 low/medium/high")
    return level


def _normalize_dataset_source_code(raw_value: str) -> str:
    return DATASET_SOURCE_CODE_ALIASES.get(raw_value, normalize_code(raw_value))


def normalize_code(value: str) -> str:
    """将展示文本转换为稳定 code。"""
    normalized = value.strip()
    normalized = re.sub(r"[\s\-/]+", "_", normalized)
    normalized = re.sub(r"[^0-9A-Za-z_]", "", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_").lower()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _require_non_empty_text(value: object, metadata_path: Path, field_name: str) -> str:
    normalized = _optional_text(value)
    if normalized is None:
        raise ImportValidationError(f"{metadata_path}: 缺少 {field_name}")
    return normalized


def _upsert_dataset_source(session: Session, *, code: str, name: str) -> tuple[DatasetSource, bool]:
    row = session.execute(select(DatasetSource).where(DatasetSource.code == code)).scalar_one_or_none()
    if row is None:
        row = DatasetSource(code=code, name=name, description=None, is_active=True)
        session.add(row)
        session.flush()
        return row, True

    row.name = name
    row.is_active = True
    return row, False


def _upsert_attack_delivery_type(session: Session, *, code: str, name: str) -> tuple[AttackDeliveryType, bool]:
    row = session.execute(select(AttackDeliveryType).where(AttackDeliveryType.code == code)).scalar_one_or_none()
    if row is None:
        row = AttackDeliveryType(code=code, name=name, description=None, is_active=True)
        session.add(row)
        session.flush()
        return row, True

    row.name = name
    row.is_active = True
    return row, False


def _upsert_risk_category(
    session: Session,
    *,
    code: str,
    name: str,
    sort_order: int,
) -> tuple[RiskCategory, bool]:
    row = session.execute(select(RiskCategory).where(RiskCategory.code == code)).scalar_one_or_none()
    if row is None:
        row = RiskCategory(
            code=code,
            name=name,
            meaning=None,
            description=None,
            sort_order=sort_order,
            is_active=True,
        )
        session.add(row)
        session.flush()
        return row, True

    row.name = name
    row.sort_order = sort_order
    row.is_active = True
    return row, False


def _upsert_risk_subtype(
    session: Session,
    *,
    category_id: int,
    code: str,
    name: str,
    sort_order: int,
) -> tuple[RiskSubtype, bool]:
    row = session.execute(select(RiskSubtype).where(RiskSubtype.code == code)).scalar_one_or_none()
    if row is None:
        row = RiskSubtype(
            category_id=category_id,
            code=code,
            name=name,
            description=None,
            sort_order=sort_order,
            is_active=True,
        )
        session.add(row)
        session.flush()
        return row, True

    row.category_id = category_id
    row.name = name
    row.sort_order = sort_order
    row.is_active = True
    return row, False


def _upsert_asset_type(session: Session, *, code: str, name: str) -> tuple[AssetType, bool]:
    row = session.execute(select(AssetType).where(AssetType.code == code)).scalar_one_or_none()
    if row is None:
        row = AssetType(code=code, name=name, description=None, is_active=True)
        session.add(row)
        session.flush()
        return row, True

    row.name = name
    row.is_active = True
    return row, False


def _upsert_benchmark_sample(
    session: Session,
    *,
    dataset_source_id: int,
    sample: PlannedSample,
    attack_delivery_type_id: int,
    risk_subtype_id: int,
    asset_type_id: int | None,
) -> tuple[BenchmarkSample, bool]:
    row = session.execute(
        select(BenchmarkSample).where(
            BenchmarkSample.dataset_source_id == dataset_source_id,
            BenchmarkSample.sample_id == sample.sample_id,
        )
    ).scalar_one_or_none()
    if row is None:
        row = BenchmarkSample(
            dataset_source_id=dataset_source_id,
            sample_id=sample.sample_id,
            sample_name=sample.sample_name,
            resource_path=sample.resource_path,
            entry_path=sample.entry_path,
            user_goal=sample.user_goal,
            attacker_goal=sample.attacker_goal,
            attacker_is_user=sample.attacker_is_user,
            attack_delivery_type_id=attack_delivery_type_id,
            risk_subtype_id=risk_subtype_id,
            risk_level=sample.risk_level,
            attack_level=sample.attack_level,
            difficulty_seed=sample.difficulty_seed,
            difficulty_score=sample.difficulty_score,
            difficulty_updated_at=None,
            asset_type_id=asset_type_id,
            expected_safe_behavior=sample.expected_safe_behavior,
            is_active=sample.is_active,
        )
        session.add(row)
        session.flush()
        return row, True

    row.sample_name = sample.sample_name
    row.resource_path = sample.resource_path
    row.entry_path = sample.entry_path
    row.user_goal = sample.user_goal
    row.attacker_goal = sample.attacker_goal
    row.attacker_is_user = sample.attacker_is_user
    row.attack_delivery_type_id = attack_delivery_type_id
    row.risk_subtype_id = risk_subtype_id
    row.risk_level = sample.risk_level
    row.attack_level = sample.attack_level
    row.difficulty_seed = sample.difficulty_seed
    row.difficulty_score = sample.difficulty_score
    row.asset_type_id = asset_type_id
    row.expected_safe_behavior = sample.expected_safe_behavior
    row.is_active = sample.is_active
    session.flush()
    return row, False


def _upsert_sample_oracle(session: Session, sample_id_ref: int, oracle: PlannedOracle) -> tuple[SampleOracle, bool]:
    row = session.execute(
        select(SampleOracle).where(
            SampleOracle.sample_id_ref == sample_id_ref,
            SampleOracle.oracle_kind == oracle.oracle_kind,
            SampleOracle.seq_no == oracle.seq_no,
        )
    ).scalar_one_or_none()
    if row is None:
        row = SampleOracle(
            sample_id_ref=sample_id_ref,
            oracle_kind=oracle.oracle_kind,
            seq_no=oracle.seq_no,
            display_text=oracle.display_text,
            evaluator_type=oracle.evaluator_type,
            evaluator_config=oracle.evaluator_config,
            is_active=oracle.is_active,
        )
        session.add(row)
        session.flush()
        return row, True

    row.display_text = oracle.display_text
    row.evaluator_type = oracle.evaluator_type
    row.evaluator_config = oracle.evaluator_config
    row.is_active = oracle.is_active
    session.flush()
    return row, False
