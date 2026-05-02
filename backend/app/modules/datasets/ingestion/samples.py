"""数据集样本扫描、归一化与样本入库逻辑。"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benchmark import AssetType, AttackDeliveryType, BenchmarkSample, DatasetSource, RiskCategory, RiskSubtype, SampleOracle
from app.modules.datasets.db_support import sync_pk_sequence
from app.modules.datasets.ingestion.errors import ImportValidationError
from app.modules.datasets.ingestion.types import (
    ImportPlan,
    ImportResult,
    PlannedOracle,
    PlannedSample,
    SampleImportPlan,
    SampleImportResult,
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
STANDARD_REQUIRED_KEYS = {
    "schema_version",
    "sample_id",
    "dataset_source_code",
    "entry_path",
    "user_goal",
    "attacker_is_user",
    "attack_delivery_type_code",
    "risk_category_code",
    "risk_subtype_code",
    "risk_level",
    "attack_level",
    "expected_safe_behavior",
    "oracles",
}
LEVEL_CODE_TO_VALUE = {"low": 1, "medium": 2, "high": 3}
DATASET_SOURCE_CODE_ALIASES = {
    "EIA": "eia",
    "VPI-bench": "vpi_bench",
    "BrowserART": "browser_art",
    "browser-art": "browser_art",
}
LEGACY_CATEGORY_DEFINITIONS = {
    "01_Confidentiality": {"code": "confidentiality", "name": "Confidentiality", "sort_order": 1},
    "02_Integrity": {"code": "integrity", "name": "Integrity", "sort_order": 2},
}
LEGACY_SUBTYPE_DEFINITIONS = {
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
KNOWN_CATEGORY_BY_CODE = {item["code"]: item for item in LEGACY_CATEGORY_DEFINITIONS.values()}
KNOWN_SUBTYPE_BY_CODE = {item["code"]: item for item in LEGACY_SUBTYPE_DEFINITIONS.values()}


@dataclass(slots=True)
class _DiscoveredMetadataFile:
    """描述扫描阶段识别出的候选元数据文件。"""

    path: Path
    fmt: str


def discover_legacy_sample_files(sample_root: Path) -> list[Path]:
    """返回 demo 目录中可导入的旧格式样本 JSON。"""
    return [item.path for item in discover_sample_metadata_files(sample_root, mode="legacy")]


def discover_sample_metadata_files(sample_root: Path, mode: str = "auto") -> list[_DiscoveredMetadataFile]:
    """发现样本目录中的元数据文件。"""
    root = sample_root.resolve()
    if not root.exists():
        raise ImportValidationError(f"样本根目录不存在: {root}")
    if mode not in {"auto", "legacy", "standard"}:
        raise ImportValidationError(f"不支持的扫描模式: {mode}")

    task_json_dirs = {path.parent for path in root.rglob("task.json") if "saved_logs" not in path.parts}
    candidates_by_dir: dict[Path, list[_DiscoveredMetadataFile]] = defaultdict(list)
    for path in sorted(root.rglob("*.json")):
        if path.name in IGNORED_JSON_FILENAMES or "saved_logs" in path.parts:
            continue
        if path.parent in task_json_dirs and path.name != "task.json":
            continue
        if path.name != "task.json" and mode == "standard":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ImportValidationError(f"JSON 解析失败: {path}: {exc}") from exc
        fmt = _detect_metadata_format(payload)
        if fmt is not None:
            candidates_by_dir[path.parent].append(_DiscoveredMetadataFile(path=path, fmt=fmt))

    discovered: list[_DiscoveredMetadataFile] = []
    for sample_dir in sorted(candidates_by_dir):
        selected = _select_metadata_file_for_dir(sample_dir, candidates_by_dir[sample_dir], mode)
        if selected is not None:
            discovered.append(selected)

    if not discovered:
        raise ImportValidationError(f"未在 {root} 下发现可导入的样本元数据")
    return discovered


def build_sample_import_plan(sample_root: Path, mode: str = "auto") -> SampleImportPlan:
    """扫描并标准化样本目录。"""
    root = sample_root.resolve()
    sample_files = discover_sample_metadata_files(root, mode=mode)
    samples = [_normalize_metadata_file(item, root) for item in sample_files]
    samples.sort(key=lambda item: (item.dataset_source_code, item.sample_id))
    return SampleImportPlan(sample_root=root, samples=samples)


build_import_plan = build_sample_import_plan


def compute_difficulty_seed(risk_level: int, attack_level: int) -> Decimal:
    """按附录公式计算初始难度。"""
    risk_norm = Decimal(risk_level - 1) / Decimal(2)
    attack_norm = Decimal(attack_level - 1) / Decimal(2)
    difficulty = Decimal("0.35") * risk_norm + Decimal("0.65") * attack_norm
    difficulty = max(Decimal("0"), min(Decimal("1"), difficulty))
    return difficulty.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def apply_sample_import_plan(session: Session, plan: SampleImportPlan) -> SampleImportResult:
    """将样本导入计划写入数据库，只负责样本与 oracle。"""
    for table_name in ("benchmark_samples", "sample_oracles"):
        sync_pk_sequence(session, table_name)

    result = SampleImportResult()
    source_cache: dict[str, DatasetSource] = {}
    delivery_cache: dict[str, AttackDeliveryType] = {}
    category_cache: dict[str, RiskCategory] = {}
    subtype_cache: dict[str, RiskSubtype] = {}
    asset_cache: dict[str, AssetType | None] = {}

    for sample in plan.samples:
        source = _require_dataset_source(session, source_cache, sample.dataset_source_code, sample.metadata_path)
        delivery = _require_attack_delivery_type(
            session,
            delivery_cache,
            sample.attack_delivery_type_code,
            sample.metadata_path,
        )
        category = _require_risk_category(session, category_cache, sample.risk_category_code, sample.metadata_path)
        subtype = _require_risk_subtype(session, subtype_cache, sample.risk_subtype_code, sample.metadata_path)
        if subtype.category_id != category.id:
            raise ImportValidationError(
                f"{sample.metadata_path}: risk_subtype_code={sample.risk_subtype_code} 不属于 "
                f"risk_category_code={sample.risk_category_code}"
            )

        asset = None
        if sample.asset_type_code is not None:
            asset = _require_asset_type(session, asset_cache, sample.asset_type_code, sample.metadata_path)

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
            _, oracle_created = _upsert_sample_oracle(session, sample_row.id, oracle)
            if oracle_created:
                result.created_oracles += 1
            else:
                result.updated_oracles += 1

    session.flush()
    return result


apply_import_plan = apply_sample_import_plan


def _normalize_metadata_file(item: _DiscoveredMetadataFile, sample_root: Path) -> PlannedSample:
    """按识别出的元数据格式分派到对应的标准化逻辑。"""
    return normalize_sample_metadata_file(item.path, sample_root, item.fmt)


def normalize_sample_metadata_file(metadata_path: Path, sample_root: Path, fmt: str) -> PlannedSample:
    """按指定格式把样本元数据归一化为 PlannedSample。"""
    if fmt == "legacy":
        return _normalize_legacy_sample(metadata_path, sample_root)
    if fmt == "standard":
        return _normalize_standard_sample(metadata_path, sample_root)
    raise ImportValidationError(f"{metadata_path}: 不支持的元数据格式 {fmt}")


def planned_sample_to_standard_task_payload(sample: PlannedSample) -> dict[str, object]:
    """把 PlannedSample 转为标准 task.json payload。"""
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "sample_id": sample.sample_id,
        "sample_name": sample.sample_name,
        "dataset_source_code": sample.dataset_source_code,
        "dataset_source_name": sample.dataset_source_name,
        "entry_path": sample.entry_path,
        "user_goal": sample.user_goal,
        "attacker_is_user": sample.attacker_is_user,
        "attack_delivery_type_code": sample.attack_delivery_type_code,
        "attack_delivery_type_name": sample.attack_delivery_type_name,
        "risk_category_code": sample.risk_category_code,
        "risk_category_name": sample.risk_category_name,
        "risk_subtype_code": sample.risk_subtype_code,
        "risk_subtype_name": sample.risk_subtype_name,
        "risk_level": _level_value_to_code(sample.risk_level, sample.metadata_path, "risk_level"),
        "attack_level": _level_value_to_code(sample.attack_level, sample.metadata_path, "attack_level"),
        "expected_safe_behavior": sample.expected_safe_behavior,
        "oracles": [
            {
                "kind": "success" if oracle.oracle_kind == 1 else "harm",
                "seq_no": oracle.seq_no,
                "display_text": oracle.display_text,
                "evaluator_type": oracle.evaluator_type,
                "evaluator_config": oracle.evaluator_config,
            }
            for oracle in sample.oracles
        ],
    }
    if sample.attacker_goal is not None:
        payload["attacker_goal"] = sample.attacker_goal
    if sample.asset_type_code is not None:
        payload["asset_type_code"] = sample.asset_type_code
    if sample.asset_type_name is not None:
        payload["asset_type_name"] = sample.asset_type_name
    if sample.risk_category_sort_order is not None:
        payload["risk_category_sort_order"] = sample.risk_category_sort_order
    if sample.risk_subtype_sort_order is not None:
        payload["risk_subtype_sort_order"] = sample.risk_subtype_sort_order
    return payload


def _normalize_legacy_sample(metadata_path: Path, sample_root: Path) -> PlannedSample:
    """把旧版样本元数据转换为统一导入结构。"""
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

    category_definition = normalize_legacy_category(primary_risk, metadata_path)
    subtype_definition = normalize_legacy_subtype(secondary_risk, metadata_path)

    risk_level = _normalize_level(payload.get("risk_level"), metadata_path, "risk_level")
    attack_level = _normalize_level(payload.get("attack_level"), metadata_path, "attack_level")
    difficulty_seed = compute_difficulty_seed(risk_level, attack_level)
    entry_path = _resolve_entry_path_from_legacy_payload(payload, sample_dir, metadata_path)
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
        oracles=_normalize_legacy_oracles(payload, metadata_path),
    )


def _normalize_standard_sample(metadata_path: Path, sample_root: Path) -> PlannedSample:
    """把标准版样本元数据转换为统一导入结构。"""
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    sample_dir = metadata_path.parent

    schema_version = _require_non_empty_text(payload.get("schema_version"), metadata_path, "schema_version")
    if schema_version != "1.0":
        raise ImportValidationError(f"{metadata_path}: schema_version 仅支持 1.0")

    sample_id = _require_non_empty_text(payload.get("sample_id"), metadata_path, "sample_id")
    dataset_source_code = _require_non_empty_text(payload.get("dataset_source_code"), metadata_path, "dataset_source_code")
    attack_delivery_type_code = _require_non_empty_text(
        payload.get("attack_delivery_type_code"),
        metadata_path,
        "attack_delivery_type_code",
    )
    risk_category_code = _require_non_empty_text(payload.get("risk_category_code"), metadata_path, "risk_category_code")
    risk_subtype_code = _require_non_empty_text(payload.get("risk_subtype_code"), metadata_path, "risk_subtype_code")
    entry_path = _require_non_empty_text(payload.get("entry_path"), metadata_path, "entry_path")
    normalized_entry_path = _coerce_relative_entry_candidate(entry_path)
    if normalized_entry_path is None:
        raise ImportValidationError(f"{metadata_path}: entry_path 必须是相对 html 路径")
    if not (sample_dir / normalized_entry_path).is_file():
        raise ImportValidationError(f"{metadata_path}: entry_path={normalized_entry_path} 不存在")

    user_goal = _require_non_empty_text(payload.get("user_goal"), metadata_path, "user_goal")
    expected_safe_behavior = _require_non_empty_text(
        payload.get("expected_safe_behavior"),
        metadata_path,
        "expected_safe_behavior",
    )
    if not isinstance(payload.get("attacker_is_user"), bool):
        raise ImportValidationError(f"{metadata_path}: attacker_is_user 必须是布尔值")

    risk_level = _normalize_level(payload.get("risk_level"), metadata_path, "risk_level")
    attack_level = _normalize_level(payload.get("attack_level"), metadata_path, "attack_level")
    difficulty_seed = compute_difficulty_seed(risk_level, attack_level)
    resource_path = sample_dir.relative_to(sample_root).as_posix()
    asset_type_code = _optional_text(payload.get("asset_type_code"))

    return PlannedSample(
        sample_id=sample_id,
        sample_name=_optional_text(payload.get("sample_name")) or sample_id,
        resource_path=resource_path,
        entry_path=normalized_entry_path,
        dataset_source_code=dataset_source_code,
        dataset_source_name=_optional_text(payload.get("dataset_source_name")) or humanize_code(dataset_source_code),
        attack_delivery_type_code=attack_delivery_type_code,
        attack_delivery_type_name=_optional_text(payload.get("attack_delivery_type_name")) or humanize_code(attack_delivery_type_code),
        risk_category_code=risk_category_code,
        risk_category_name=_optional_text(payload.get("risk_category_name")) or default_category_name(risk_category_code),
        risk_category_sort_order=_optional_sort_order(
            payload.get("risk_category_sort_order"),
            metadata_path,
            "risk_category_sort_order",
        )
        or default_category_sort_order(risk_category_code),
        risk_subtype_code=risk_subtype_code,
        risk_subtype_name=_optional_text(payload.get("risk_subtype_name")) or default_subtype_name(risk_subtype_code),
        risk_subtype_sort_order=_optional_sort_order(
            payload.get("risk_subtype_sort_order"),
            metadata_path,
            "risk_subtype_sort_order",
        )
        or default_subtype_sort_order(risk_subtype_code),
        asset_type_code=asset_type_code,
        asset_type_name=(
            _optional_text(payload.get("asset_type_name"))
            or (humanize_code(asset_type_code) if asset_type_code else None)
        ),
        user_goal=user_goal,
        attacker_goal=_optional_text(payload.get("attacker_goal")),
        attacker_is_user=payload["attacker_is_user"],
        risk_level=risk_level,
        attack_level=attack_level,
        difficulty_seed=difficulty_seed,
        difficulty_score=difficulty_seed,
        expected_safe_behavior=expected_safe_behavior,
        metadata_path=metadata_path,
        oracles=_normalize_standard_oracles(payload, metadata_path),
    )


def _normalize_legacy_oracles(payload: dict[str, object], metadata_path: Path) -> list[PlannedOracle]:
    """解析旧版样本中的 success/harm 判定规则列表。"""
    oracles: list[PlannedOracle] = []
    for oracle_kind, field_name in ((1, "success_oracle"), (2, "harm_oracle")):
        raw_list = payload.get(field_name)
        if not isinstance(raw_list, list):
            raise ImportValidationError(f"{metadata_path}: {field_name} 必须是数组")
        if not raw_list:
            if oracle_kind == 1:
                oracles.append(
                    PlannedOracle(
                        oracle_kind=1,
                        seq_no=1,
                        display_text="Runtime finalize completed.",
                        evaluator_type="completion_signal",
                        evaluator_config={"source": "finalize.done"},
                    )
                )
            continue

        object_conditions: list[dict[str, object]] = []
        text_items: list[str] = []
        for index, item in enumerate(raw_list, start=1):
            if isinstance(item, dict):
                object_conditions.append(_normalize_event_condition(item, metadata_path, f"{field_name}[{index}]"))
                continue
            text = _optional_text(item)
            if not text:
                raise ImportValidationError(f"{metadata_path}: {field_name}[{index}] 必须是非空字符串或对象")
            text_items.append(text)

        seq_no = 1
        if object_conditions:
            oracles.append(
                PlannedOracle(
                    oracle_kind=oracle_kind,
                    seq_no=seq_no,
                    display_text=_event_trace_display_text(oracle_kind, len(object_conditions)),
                    evaluator_type="event_trace_match",
                    evaluator_config={"ordered": True, "conditions": object_conditions},
                )
            )
            seq_no += 1

        for text in text_items:
            oracles.append(
                PlannedOracle(
                    oracle_kind=oracle_kind,
                    seq_no=seq_no,
                    display_text=text,
                    evaluator_type="manual_review",
                    evaluator_config={"criteria": text},
                )
            )
            seq_no += 1
    if not oracles:
        raise ImportValidationError(f"{metadata_path}: success_oracle/harm_oracle 至少需要生成一条规则")
    return oracles


def _normalize_event_condition(item: dict[str, object], metadata_path: Path, field_name: str) -> dict[str, object]:
    """把 legacy 对象型 oracle 条件规范成 event_trace_match 条件。"""
    event_type = _require_non_empty_text(item.get("event_type"), metadata_path, f"{field_name}.event_type")
    condition: dict[str, object] = {"event_type": event_type}
    target = item.get("target")
    if target is not None:
        if not isinstance(target, dict):
            raise ImportValidationError(f"{metadata_path}: {field_name}.target 必须是对象")
        condition["target"] = target
    if "value_equals" in item:
        condition["value_equals"] = item["value_equals"]
    if "ordered" in item:
        condition["ordered"] = bool(item["ordered"])
    return condition


def _event_trace_display_text(oracle_kind: int, condition_count: int) -> str:
    """生成结构化事件 oracle 的人类可读说明。"""
    kind_text = "success" if oracle_kind == 1 else "harm"
    return f"Match {condition_count} {kind_text} event condition(s)."


def _normalize_standard_oracles(payload: dict[str, object], metadata_path: Path) -> list[PlannedOracle]:
    """解析标准版样本中的判定规则列表。"""
    raw_oracles = payload.get("oracles")
    if not isinstance(raw_oracles, list) or not raw_oracles:
        raise ImportValidationError(f"{metadata_path}: oracles 必须是非空数组")

    oracles: list[PlannedOracle] = []
    seen_keys: set[tuple[int, int]] = set()
    for index, item in enumerate(raw_oracles, start=1):
        if not isinstance(item, dict):
            raise ImportValidationError(f"{metadata_path}: oracles[{index}] 必须是对象")
        kind = _optional_text(item.get("kind"))
        if kind not in {"success", "harm"}:
            raise ImportValidationError(f"{metadata_path}: oracles[{index}].kind 仅支持 success/harm")
        seq_no = item.get("seq_no")
        if not isinstance(seq_no, int) or seq_no <= 0:
            raise ImportValidationError(f"{metadata_path}: oracles[{index}].seq_no 必须是正整数")
        display_text = _require_non_empty_text(item.get("display_text"), metadata_path, f"oracles[{index}].display_text")
        evaluator_type = _require_non_empty_text(item.get("evaluator_type"), metadata_path, f"oracles[{index}].evaluator_type")
        evaluator_config = item.get("evaluator_config")
        if not isinstance(evaluator_config, dict):
            raise ImportValidationError(f"{metadata_path}: oracles[{index}].evaluator_config 必须是对象")
        oracle_kind = 1 if kind == "success" else 2
        dedupe_key = (oracle_kind, seq_no)
        if dedupe_key in seen_keys:
            raise ImportValidationError(
                f"{metadata_path}: 重复的 oracle kind/seq_no 组合 {kind}/{seq_no}"
            )
        seen_keys.add(dedupe_key)
        oracles.append(
            PlannedOracle(
                oracle_kind=oracle_kind,
                seq_no=seq_no,
                display_text=display_text,
                evaluator_type=evaluator_type,
                evaluator_config=evaluator_config,
            )
        )

    return oracles


def _resolve_entry_path_from_legacy_payload(payload: dict[str, object], sample_dir: Path, metadata_path: Path) -> str:
    """为旧版样本推断可执行入口文件路径。"""
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
    """从目标描述文本中提取可能的 HTML 入口候选。"""
    quoted_segments = re.findall(r"""['"]([^'"]+?\.html(?:[^'"]*)?)['"]""", text)
    candidates: list[str] = []
    for segment in quoted_segments:
        candidate = _coerce_relative_entry_candidate(segment)
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _coerce_relative_entry_candidate(raw_value: str) -> str | None:
    """把入口候选值规范为相对 HTML 路径。"""
    value = raw_value.strip()
    if not value:
        return None

    if "://" in value:
        parsed = urlparse(value)
        value = parsed.path

    value = value.strip().replace("\\", "/").lstrip("/")
    if not value or not value.endswith(".html"):
        return None
    if Path(value).is_absolute():
        return None
    if ".." in Path(value).parts:
        return None
    return value


def _normalize_level(value: object, metadata_path: Path, field_name: str) -> int:
    """把 low/medium/high 风险级别转换为数值档位。"""
    normalized = _optional_text(value)
    level = LEVEL_CODE_TO_VALUE.get(normalized or "")
    if level is None:
        raise ImportValidationError(f"{metadata_path}: {field_name} 仅支持 low/medium/high")
    return level


def _level_value_to_code(value: int, metadata_path: Path, field_name: str) -> str:
    """把数值档位转换回 low/medium/high。"""
    for code, numeric in LEVEL_CODE_TO_VALUE.items():
        if numeric == value:
            return code
    raise ImportValidationError(f"{metadata_path}: {field_name} 数值档位不合法")


def normalize_legacy_category(raw_value: str, metadata_path: Path) -> dict[str, object]:
    """把 legacy primary_risk 归一化为统一大类定义。"""
    definition = LEGACY_CATEGORY_DEFINITIONS.get(raw_value)
    if definition is not None:
        return dict(definition)

    match = re.fullmatch(r"(?P<order>\d+)_+(?P<label>.+)", raw_value.strip())
    if match is None:
        raise ImportValidationError(f"{metadata_path}: 不支持的 primary_risk={raw_value}")
    label = match.group("label")
    return {
        "code": normalize_code(label),
        "name": humanize_code(label),
        "sort_order": int(match.group("order")),
    }


def normalize_legacy_subtype(raw_value: str, metadata_path: Path) -> dict[str, object]:
    """把 legacy secondary_risk 归一化为统一子类定义。"""
    definition = LEGACY_SUBTYPE_DEFINITIONS.get(raw_value)
    if definition is not None:
        return dict(definition)

    match = re.fullmatch(r"(?P<prefix>[A-Za-z])(?P<order>\d+)_+(?P<label>.+)", raw_value.strip())
    if match is None:
        raise ImportValidationError(f"{metadata_path}: 不支持的 secondary_risk={raw_value}")
    prefix = match.group("prefix").upper()
    order = int(match.group("order"))
    label = match.group("label")
    return {
        "code": f"{prefix}{order}_{normalize_code(label)}",
        "name": humanize_code(label),
        "sort_order": order,
    }


def _optional_sort_order(value: object, metadata_path: Path, field_name: str) -> int | None:
    """解析可选排序字段。"""
    if value is None:
        return None
    if not isinstance(value, int) or value <= 0:
        raise ImportValidationError(f"{metadata_path}: {field_name} 必须是正整数")
    return value


def _normalize_dataset_source_code(raw_value: str) -> str:
    """规范旧数据源名称并映射为稳定 code。"""
    return DATASET_SOURCE_CODE_ALIASES.get(raw_value, normalize_code(raw_value))


def normalize_code(value: str) -> str:
    """将展示文本转换为稳定 code。"""
    normalized = value.strip()
    normalized = re.sub(r"[\s\-/]+", "_", normalized)
    normalized = re.sub(r"[^0-9A-Za-z_]", "", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_").lower()


def humanize_code(value: str) -> str:
    """将 code 转换为基本可读名称。"""
    parts = [item for item in re.split(r"[_\-/]+", value.strip()) if item]
    if not parts:
        return value
    readable: list[str] = []
    for item in parts:
        if re.fullmatch(r"[A-Z]{2,}|\d+", item):
            readable.append(item)
        elif re.fullmatch(r"[A-Za-z]\d+", item):
            readable.append(item.upper())
        else:
            readable.append(item.capitalize())
    return " ".join(readable)


def default_category_name(code: str) -> str:
    """返回风险大类 code 对应的默认展示名称。"""
    return KNOWN_CATEGORY_BY_CODE.get(code, {}).get("name", humanize_code(code))


def default_category_sort_order(code: str) -> int | None:
    """返回风险大类 code 对应的默认排序值。"""
    return KNOWN_CATEGORY_BY_CODE.get(code, {}).get("sort_order")


def default_subtype_name(code: str) -> str:
    """返回风险子类 code 对应的默认展示名称。"""
    return KNOWN_SUBTYPE_BY_CODE.get(code, {}).get("name", humanize_code(code))


def default_subtype_sort_order(code: str) -> int | None:
    """返回风险子类 code 对应的默认排序值。"""
    return KNOWN_SUBTYPE_BY_CODE.get(code, {}).get("sort_order")


def _optional_text(value: object) -> str | None:
    """提取可选字符串字段并去除空白。"""
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _require_non_empty_text(value: object, metadata_path: Path, field_name: str) -> str:
    """提取必填字符串字段，缺失时抛出导入异常。"""
    normalized = _optional_text(value)
    if normalized is None:
        raise ImportValidationError(f"{metadata_path}: 缺少 {field_name}")
    return normalized


def _detect_metadata_format(payload: object) -> str | None:
    """识别元数据对象属于 legacy 还是 standard 格式。"""
    if not isinstance(payload, dict):
        return None
    if STANDARD_REQUIRED_KEYS.issubset(payload):
        return "standard"
    if LEGACY_REQUIRED_KEYS.issubset(payload):
        return "legacy"
    return None


def detect_metadata_format(payload: object) -> str | None:
    """对外暴露元数据格式识别。"""
    return _detect_metadata_format(payload)


def _select_metadata_file_for_dir(
    sample_dir: Path,
    candidates: list[_DiscoveredMetadataFile],
    mode: str,
) -> _DiscoveredMetadataFile | None:
    """在样本目录下选出当前模式允许导入的唯一元数据文件。"""
    if mode == "auto":
        standard = [item for item in candidates if item.fmt == "standard"]
        legacy = [item for item in candidates if item.fmt == "legacy"]
        if standard and legacy:
            raise ImportValidationError(f"{sample_dir}: 同目录同时存在 standard 与 legacy 元数据")
        if len(standard) > 1 or len(legacy) > 1:
            raise ImportValidationError(f"{sample_dir}: 同目录存在多个可导入元数据文件")
        return standard[0] if standard else (legacy[0] if legacy else None)

    filtered = [item for item in candidates if item.fmt == mode]
    if len(filtered) > 1:
        raise ImportValidationError(f"{sample_dir}: 同目录存在多个 {mode} 元数据文件")
    return filtered[0] if filtered else None


def _require_dataset_source(
    session: Session,
    cache: dict[str, DatasetSource],
    code: str,
    metadata_path: Path,
) -> DatasetSource:
    """校验数据源已注册，并优先复用查询缓存。"""
    row = cache.get(code)
    if row is not None:
        return row
    row = session.execute(select(DatasetSource).where(DatasetSource.code == code)).scalar_one_or_none()
    if row is None:
        raise ImportValidationError(f"{metadata_path}: dataset_source_code={code} 未在数据库中注册")
    cache[code] = row
    return row


def _require_attack_delivery_type(
    session: Session,
    cache: dict[str, AttackDeliveryType],
    code: str,
    metadata_path: Path,
) -> AttackDeliveryType:
    """校验攻击投递方式已注册，并优先复用查询缓存。"""
    row = cache.get(code)
    if row is not None:
        return row
    row = session.execute(select(AttackDeliveryType).where(AttackDeliveryType.code == code)).scalar_one_or_none()
    if row is None:
        raise ImportValidationError(f"{metadata_path}: attack_delivery_type_code={code} 未在数据库中注册")
    cache[code] = row
    return row


def _require_risk_category(
    session: Session,
    cache: dict[str, RiskCategory],
    code: str,
    metadata_path: Path,
) -> RiskCategory:
    """校验风险大类已注册，并优先复用查询缓存。"""
    row = cache.get(code)
    if row is not None:
        return row
    row = session.execute(select(RiskCategory).where(RiskCategory.code == code)).scalar_one_or_none()
    if row is None:
        raise ImportValidationError(f"{metadata_path}: risk_category_code={code} 未在数据库中注册")
    cache[code] = row
    return row


def _require_risk_subtype(
    session: Session,
    cache: dict[str, RiskSubtype],
    code: str,
    metadata_path: Path,
) -> RiskSubtype:
    """校验风险子类已注册，并优先复用查询缓存。"""
    row = cache.get(code)
    if row is not None:
        return row
    row = session.execute(select(RiskSubtype).where(RiskSubtype.code == code)).scalar_one_or_none()
    if row is None:
        raise ImportValidationError(f"{metadata_path}: risk_subtype_code={code} 未在数据库中注册")
    cache[code] = row
    return row


def _require_asset_type(
    session: Session,
    cache: dict[str, AssetType | None],
    code: str,
    metadata_path: Path,
) -> AssetType:
    """校验资产类型已注册，并优先复用查询缓存。"""
    cached = cache.get(code)
    if cached is not None:
        return cached
    row = session.execute(select(AssetType).where(AssetType.code == code)).scalar_one_or_none()
    if row is None:
        raise ImportValidationError(f"{metadata_path}: asset_type_code={code} 未在数据库中注册")
    cache[code] = row
    return row


def _upsert_benchmark_sample(
    session: Session,
    *,
    dataset_source_id: int,
    sample: PlannedSample,
    attack_delivery_type_id: int,
    risk_subtype_id: int,
    asset_type_id: int | None,
) -> tuple[BenchmarkSample, bool]:
    """按来源与样本编号幂等写入样本主记录。"""
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
    row.asset_type_id = asset_type_id
    row.expected_safe_behavior = sample.expected_safe_behavior
    row.is_active = sample.is_active
    session.flush()
    return row, False


def _upsert_sample_oracle(session: Session, sample_id_ref: int, oracle: PlannedOracle) -> tuple[SampleOracle, bool]:
    """按样本、规则类型与序号幂等写入判定规则。"""
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
