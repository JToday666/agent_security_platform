"""版本化数据集元数据的 JSON 读写、同步与入库逻辑。"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benchmark import (
    AssetType,
    AttackDeliveryType,
    AttackScenario,
    AttackScenarioRiskDomain,
    DatasetSource,
    RiskCategory,
    RiskSubtype,
    RiskSubtypeDisplayMeta,
)
from app.modules.datasets.db_support import sync_pk_sequence
from app.modules.datasets.ingestion.errors import ImportValidationError
from app.modules.datasets.ingestion.samples import (
    build_sample_import_plan,
    default_category_name,
    default_category_sort_order,
    default_subtype_name,
    default_subtype_sort_order,
    humanize_code,
)
from app.modules.datasets.ingestion.types import (
    AttackScenarioRecord,
    AssetTypeRecord,
    AttackDeliveryTypeRecord,
    DatasetSourceRecord,
    DisplayMetaRecord,
    MetadataBundle,
    MetadataImportResult,
    RiskCategoryRecord,
    RiskSubtypeRecord,
)

DEFAULT_ATTACK_SCENARIOS: tuple[AttackScenarioRecord, ...] = (
    AttackScenarioRecord(
        code="prompt_injection",
        name="提示注入",
        description="覆盖直接和间接提示注入攻击。",
        sort_order=1,
        translations={
            "en-US": {
                "name": "Prompt Injection",
                "description": (
                    "Covers direct and indirect prompt injection attacks."
                ),
            },
            "fr-FR": {
                "name": "Injection de prompt",
                "description": (
                    "Couvre les attaques d’injection de prompt directes et "
                    "indirectes."
                ),
            },
            "es-ES": {
                "name": "Inyección de prompts",
                "description": (
                    "Cubre ataques de inyección de prompts directos e "
                    "indirectos."
                ),
            },
            "ja-JP": {
                "name": "プロンプトインジェクション",
                "description": (
                    "直接・間接のプロンプトインジェクション攻撃を扱う。"
                ),
            },
        },
    ),
    AttackScenarioRecord(
        code="model_abuse_and_unauthorized_actions",
        name="模型滥用与越权行为",
        description="覆盖模型滥用、违规生成和越权操作。",
        sort_order=2,
        translations={
            "en-US": {
                "name": "Model Abuse and Unauthorized Actions",
                "description": (
                    "Covers model abuse, disallowed generation, and "
                    "unauthorized operations."
                ),
            },
            "fr-FR": {
                "name": "Abus du modèle et actions non autorisées",
                "description": (
                    "Couvre l’abus du modèle, les générations interdites et "
                    "les opérations non autorisées."
                ),
            },
            "es-ES": {
                "name": "Abuso del modelo y acciones no autorizadas",
                "description": (
                    "Cubre abuso del modelo, generación no permitida y "
                    "operaciones no autorizadas."
                ),
            },
            "ja-JP": {
                "name": "モデル悪用と無許可行動",
                "description": (
                    "モデル悪用、禁止コンテンツ生成、無許可操作を扱う。"
                ),
            },
        },
    ),
    AttackScenarioRecord(
        code="knowledge_base_poisoning",
        name="知识库投毒",
        description="覆盖知识库污染与检索误导。",
        sort_order=3,
        translations={
            "en-US": {
                "name": "Knowledge Base Poisoning",
                "description": (
                    "Covers knowledge base contamination and retrieval "
                    "misdirection."
                ),
            },
            "fr-FR": {
                "name": "Empoisonnement de la base de connaissances",
                "description": (
                    "Couvre la contamination de bases de connaissances et "
                    "l’orientation trompeuse de la récupération."
                ),
            },
            "es-ES": {
                "name": "Envenenamiento de la base de conocimiento",
                "description": (
                    "Cubre contaminación de bases de conocimiento y desvíos "
                    "engañosos en la recuperación."
                ),
            },
            "ja-JP": {
                "name": "ナレッジベース汚染",
                "description": (
                    "ナレッジベースの汚染と検索結果の誘導を扱う。"
                ),
            },
        },
    ),
    AttackScenarioRecord(
        code="tool_call_hijacking",
        name="工具调用劫持",
        description="覆盖工具调用参数和流程劫持。",
        sort_order=4,
        translations={
            "en-US": {
                "name": "Tool Call Hijacking",
                "description": (
                    "Covers hijacking of tool-call parameters and execution "
                    "flow."
                ),
            },
            "fr-FR": {
                "name": "Détournement d’appels d’outils",
                "description": (
                    "Couvre le détournement des paramètres d’appel d’outils "
                    "et du flux d’exécution."
                ),
            },
            "es-ES": {
                "name": "Secuestro de llamadas a herramientas",
                "description": (
                    "Cubre el secuestro de parámetros de llamadas a "
                    "herramientas y del flujo de ejecución."
                ),
            },
            "ja-JP": {
                "name": "ツール呼び出しハイジャック",
                "description": (
                    "ツール呼び出しパラメータと実行フローの乗っ取りを扱う。"
                ),
            },
        },
    ),
)

PROMPT_INJECTION_RISK_DOMAINS = {
    "confidentiality",
    "integrity",
    "availability_and_destructive_harm",
}
MODEL_ABUSE_RISK_DOMAINS = {
    "unauthorized_execution_and_system_control",
    "fraud_impersonation_and_social_engineering",
    "content_and_societal_harm",
    "harmful_search_and_reconnaissance",
}
DEFAULT_SCENARIO_BY_RISK_DOMAIN = {
    **{
        risk_domain_code: "prompt_injection"
        for risk_domain_code in PROMPT_INJECTION_RISK_DOMAINS
    },
    **{
        risk_domain_code: "model_abuse_and_unauthorized_actions"
        for risk_domain_code in MODEL_ABUSE_RISK_DOMAINS
    },
}


def load_metadata_bundle(registry_root: Path) -> MetadataBundle:
    """从 registry/display_meta 目录读取元数据。"""
    root = registry_root.resolve()
    bundle = MetadataBundle(
        dataset_sources=[
            DatasetSourceRecord(**item)
            for item in _load_json_list(root / "registry" / "dataset_sources.json")
        ],
        attack_delivery_types=[
            AttackDeliveryTypeRecord(**item)
            for item in _load_json_list(
                root / "registry" / "attack_delivery_types.json"
            )
        ],
        asset_types=[
            AssetTypeRecord(**item)
            for item in _load_json_list(root / "registry" / "asset_types.json")
        ],
        attack_scenarios=[
            AttackScenarioRecord(**item)
            for item in _load_json_list(root / "registry" / "attack_scenarios.json")
        ],
        risk_categories=[
            RiskCategoryRecord(**item)
            for item in _load_json_list(root / "registry" / "risk_categories.json")
        ],
        risk_subtypes=[
            RiskSubtypeRecord(**item)
            for item in _load_json_list(root / "registry" / "risk_subtypes.json")
        ],
    )

    display_meta_dir = root / "display_meta"
    if display_meta_dir.exists():
        for path in sorted(display_meta_dir.glob("*.json")):
            if path.name == "index.json":
                continue
            payload = _load_json_object(path)
            record = DisplayMetaRecord(**payload)
            bundle.display_meta_by_code[record.subtype_code] = record

    return bundle


def write_metadata_bundle(registry_root: Path, bundle: MetadataBundle) -> None:
    """将元数据写回 registry/display_meta 目录。"""
    root = registry_root.resolve()
    (root / "registry").mkdir(parents=True, exist_ok=True)
    (root / "display_meta").mkdir(parents=True, exist_ok=True)

    _write_json(
        root / "registry" / "dataset_sources.json",
        [
            _record_payload(item)
            for item in sorted(bundle.dataset_sources, key=lambda item: item.code)
        ],
    )
    _write_json(
        root / "registry" / "attack_delivery_types.json",
        [
            _record_payload(item)
            for item in sorted(bundle.attack_delivery_types, key=lambda item: item.code)
        ],
    )
    _write_json(
        root / "registry" / "asset_types.json",
        [
            _record_payload(item)
            for item in sorted(bundle.asset_types, key=lambda item: item.code)
        ],
    )
    _write_json(
        root / "registry" / "attack_scenarios.json",
        [
            _record_payload(item)
            for item in sorted(
                bundle.attack_scenarios,
                key=lambda item: ((item.sort_order or 999), item.code),
            )
        ],
    )
    _write_json(
        root / "registry" / "risk_categories.json",
        [
            _record_payload(item)
            for item in sorted(
                bundle.risk_categories,
                key=lambda item: ((item.sort_order or 999), item.code),
            )
        ],
    )
    _write_json(
        root / "registry" / "risk_subtypes.json",
        [
            _record_payload(item)
            for item in sorted(
                bundle.risk_subtypes,
                key=lambda item: ((item.sort_order or 999), item.code),
            )
        ],
    )
    for code, record in sorted(bundle.display_meta_by_code.items()):
        _write_json(root / "display_meta" / f"{code}.json", _record_payload(record))
    write_display_meta_index(root, bundle)


def _record_payload(record) -> dict[str, object]:
    """Convert a metadata dataclass to JSON while omitting empty translations."""
    payload = asdict(record)
    if not payload.get("translations"):
        payload.pop("translations", None)
    return payload


def _merge_default_attack_scenarios(
    records: list[AttackScenarioRecord],
) -> list[AttackScenarioRecord]:
    """合并默认四个攻击场景和 registry 中的覆盖项。"""
    merged = {item.code: item for item in DEFAULT_ATTACK_SCENARIOS}
    for item in records:
        default = merged.get(item.code)
        merged[item.code] = (
            _merge_attack_scenario_record(default, item) if default else item
        )
    return sorted(
        merged.values(),
        key=lambda item: ((item.sort_order or 999), item.code),
    )


def _merge_attack_scenario_record(
    default: AttackScenarioRecord,
    override: AttackScenarioRecord,
) -> AttackScenarioRecord:
    """Merge registry fields while preserving default i18n fallbacks."""
    return AttackScenarioRecord(
        code=override.code,
        name=override.name,
        description=(
            override.description
            if override.description is not None
            else default.description
        ),
        sort_order=(
            override.sort_order
            if override.sort_order is not None
            else default.sort_order
        ),
        is_active=override.is_active,
        translations=_merge_translation_maps(
            default.translations, override.translations
        ),
    )


def _merge_translation_maps(
    default: dict[str, dict[str, object]],
    override: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    merged = {locale: dict(values) for locale, values in default.items()}
    for locale, values in override.items():
        next_values = dict(merged.get(locale, {}))
        next_values.update(values)
        merged[locale] = next_values
    return merged


def _resolve_attack_scenario_code(
    explicit_code: str | None,
    risk_category_code: str,
) -> str:
    """解析评测项归属场景；旧七类风险域允许按默认映射补齐。"""
    if explicit_code:
        return explicit_code
    default_code = DEFAULT_SCENARIO_BY_RISK_DOMAIN.get(risk_category_code)
    if default_code:
        return default_code
    raise ImportValidationError(
        "risk_subtypes.json: 新评测项必须声明 attack_scenario_code"
    )


def write_display_meta_index(registry_root: Path, bundle: MetadataBundle) -> Path:
    """根据当前元数据生成 display_meta/index.json 导航索引。"""
    root = registry_root.resolve()
    index_path = root / "display_meta" / "index.json"
    _write_json(index_path, build_display_meta_index(bundle))
    return index_path


def build_display_meta_index(bundle: MetadataBundle) -> list[dict[str, object]]:
    """生成便于浏览的 display_meta 索引。"""
    category_by_code = {item.code: item for item in bundle.risk_categories}
    subtype_by_code = {item.code: item for item in bundle.risk_subtypes}
    known_codes = set(subtype_by_code) | set(bundle.display_meta_by_code)

    def sort_key(code: str) -> tuple[int, int, str]:
        subtype = subtype_by_code.get(code)
        category = category_by_code.get(subtype.category_code) if subtype else None
        return (
            (
                category.sort_order
                if category and category.sort_order is not None
                else 999
            ),
            subtype.sort_order if subtype and subtype.sort_order is not None else 999,
            code,
        )

    index_rows: list[dict[str, object]] = []
    for code in sorted(known_codes, key=sort_key):
        subtype = subtype_by_code.get(code)
        display_meta = bundle.display_meta_by_code.get(code)
        index_rows.append(
            {
                "subtype_code": code,
                "category_code": subtype.category_code if subtype else None,
                "name": subtype.name if subtype else humanize_code(code),
                "short_description": (
                    display_meta.short_description if display_meta else None
                ),
                "path": f"display_meta/{code}.json",
            }
        )
    return index_rows


def build_metadata_bundle_from_samples(
    sample_root: Path, registry_root: Path, mode: str = "auto"
) -> MetadataBundle:
    """根据样本目录生成合并后的 metadata bundle，但不落盘。"""
    bundle = load_metadata_bundle(registry_root)
    source_by_code = {item.code: item for item in bundle.dataset_sources}
    delivery_by_code = {item.code: item for item in bundle.attack_delivery_types}
    asset_by_code = {item.code: item for item in bundle.asset_types}
    scenario_by_code = {
        item.code: item for item in _merge_default_attack_scenarios(bundle.attack_scenarios)
    }
    category_by_code = {item.code: item for item in bundle.risk_categories}
    subtype_by_code = {item.code: item for item in bundle.risk_subtypes}
    display_meta_by_code = dict(bundle.display_meta_by_code)

    sample_plan = build_sample_import_plan(sample_root, mode=mode)
    for sample in sample_plan.samples:
        if sample.dataset_source_code not in source_by_code:
            source_by_code[sample.dataset_source_code] = DatasetSourceRecord(
                code=sample.dataset_source_code,
                name=sample.dataset_source_name
                or humanize_code(sample.dataset_source_code),
            )
        if sample.attack_delivery_type_code not in delivery_by_code:
            delivery_by_code[sample.attack_delivery_type_code] = (
                AttackDeliveryTypeRecord(
                    code=sample.attack_delivery_type_code,
                    name=sample.attack_delivery_type_name
                    or humanize_code(sample.attack_delivery_type_code),
                )
            )
        if sample.asset_type_code and sample.asset_type_code not in asset_by_code:
            asset_by_code[sample.asset_type_code] = AssetTypeRecord(
                code=sample.asset_type_code,
                name=sample.asset_type_name or humanize_code(sample.asset_type_code),
            )
        if sample.risk_category_code not in category_by_code:
            category_by_code[sample.risk_category_code] = RiskCategoryRecord(
                code=sample.risk_category_code,
                name=sample.risk_category_name
                or default_category_name(sample.risk_category_code),
                sort_order=sample.risk_category_sort_order
                or default_category_sort_order(sample.risk_category_code),
            )
        if sample.risk_subtype_code not in subtype_by_code:
            subtype_by_code[sample.risk_subtype_code] = RiskSubtypeRecord(
                code=sample.risk_subtype_code,
                category_code=sample.risk_category_code,
                attack_scenario_code=_resolve_attack_scenario_code(
                    sample.attack_scenario_code, sample.risk_category_code
                ),
                name=sample.risk_subtype_name
                or default_subtype_name(sample.risk_subtype_code),
                sort_order=sample.risk_subtype_sort_order
                or default_subtype_sort_order(sample.risk_subtype_code),
            )
        if sample.risk_subtype_code not in display_meta_by_code:
            display_meta_by_code[sample.risk_subtype_code] = DisplayMetaRecord(
                subtype_code=sample.risk_subtype_code
            )

    for subtype in subtype_by_code.values():
        if subtype.attack_scenario_code:
            continue
        subtype.attack_scenario_code = _resolve_attack_scenario_code(
            subtype.attack_scenario_code, subtype.category_code
        )

    return MetadataBundle(
        dataset_sources=list(source_by_code.values()),
        attack_delivery_types=list(delivery_by_code.values()),
        attack_scenarios=list(scenario_by_code.values()),
        asset_types=list(asset_by_code.values()),
        risk_categories=list(category_by_code.values()),
        risk_subtypes=list(subtype_by_code.values()),
        display_meta_by_code=display_meta_by_code,
    )


def sync_metadata_from_samples(
    sample_root: Path, registry_root: Path, mode: str = "auto"
) -> MetadataBundle:
    """从样本目录补齐 registry 与 display_meta 骨架。"""
    bundle = build_metadata_bundle_from_samples(sample_root, registry_root, mode=mode)
    write_metadata_bundle(registry_root, bundle)
    return bundle


sync_registry_from_samples = sync_metadata_from_samples


def build_metadata_bundle_from_database(session: Session) -> MetadataBundle:
    """从数据库导出当前元数据。"""
    categories = (
        session.execute(
            select(RiskCategory).order_by(
                RiskCategory.sort_order.asc().nullslast(), RiskCategory.code.asc()
            )
        )
        .scalars()
        .all()
    )
    subtypes = (
        session.execute(
            select(RiskSubtype).order_by(
                RiskSubtype.sort_order.asc().nullslast(), RiskSubtype.code.asc()
            )
        )
        .scalars()
        .all()
    )
    category_code_by_id = {item.id: item.code for item in categories}
    scenarios = (
        session.execute(
            select(AttackScenario).order_by(
                AttackScenario.sort_order.asc().nullslast(),
                AttackScenario.code.asc(),
            )
        )
        .scalars()
        .all()
    )
    scenario_code_by_id = {item.id: item.code for item in scenarios}

    bundle = MetadataBundle(
        attack_scenarios=[
            AttackScenarioRecord(
                code=item.code,
                name=item.name,
                description=item.description,
                sort_order=item.sort_order,
                is_active=item.is_active,
                translations=dict(item.translations or {}),
            )
            for item in scenarios
        ],
        dataset_sources=[
            DatasetSourceRecord(
                code=item.code,
                name=item.name,
                description=item.description,
                is_active=item.is_active,
                translations=dict(item.translations or {}),
            )
            for item in session.execute(
                select(DatasetSource).order_by(DatasetSource.code.asc())
            ).scalars()
        ],
        attack_delivery_types=[
            AttackDeliveryTypeRecord(
                code=item.code,
                name=item.name,
                description=item.description,
                is_active=item.is_active,
                translations=dict(item.translations or {}),
            )
            for item in session.execute(
                select(AttackDeliveryType).order_by(AttackDeliveryType.code.asc())
            ).scalars()
        ],
        asset_types=[
            AssetTypeRecord(
                code=item.code,
                name=item.name,
                description=item.description,
                is_active=item.is_active,
                translations=dict(item.translations or {}),
            )
            for item in session.execute(
                select(AssetType).order_by(AssetType.code.asc())
            ).scalars()
        ],
        risk_categories=[
            RiskCategoryRecord(
                code=item.code,
                name=item.name,
                meaning=item.meaning,
                description=item.description,
                sort_order=item.sort_order,
                is_active=item.is_active,
                translations=dict(item.translations or {}),
            )
            for item in categories
        ],
        risk_subtypes=[
            RiskSubtypeRecord(
                code=item.code,
                category_code=category_code_by_id[item.category_id],
                attack_scenario_code=scenario_code_by_id.get(
                    item.attack_scenario_id
                ),
                name=item.name,
                sort_order=item.sort_order,
                is_active=item.is_active,
                translations=dict(item.translations or {}),
            )
            for item in subtypes
        ],
    )

    subtype_code_by_id = {item.id: item.code for item in subtypes}
    for item in session.execute(select(RiskSubtypeDisplayMeta)).scalars():
        subtype_code = subtype_code_by_id.get(item.subtype_id)
        if subtype_code is None:
            continue
        bundle.display_meta_by_code[subtype_code] = DisplayMetaRecord(
            subtype_code=subtype_code,
            short_description=item.short_description,
            full_description=item.full_description,
            highlights=list(item.highlights or []),
            scenarios=list(item.scenarios or []),
            resources=list(item.resources or []),
            media=list(item.media or []),
            translations=dict(item.translations or {}),
        )

    return bundle


def apply_metadata_bundle(
    session: Session, bundle: MetadataBundle
) -> MetadataImportResult:
    """将 JSON 元数据幂等写入数据库。"""
    for table_name in (
        "dataset_sources",
        "attack_delivery_types",
        "attack_scenarios",
        "asset_types",
        "risk_categories",
        "risk_subtypes",
    ):
        sync_pk_sequence(session, table_name)

    result = MetadataImportResult()
    category_rows: dict[str, RiskCategory] = {}
    scenario_rows: dict[str, AttackScenario] = {}
    subtype_rows: dict[str, RiskSubtype] = {}

    for item in bundle.dataset_sources:
        _, created = _upsert_dataset_source(session, item)
        if created:
            result.created_sources += 1
        else:
            result.updated_sources += 1

    for item in bundle.attack_delivery_types:
        _, created = _upsert_attack_delivery_type(session, item)
        if created:
            result.created_delivery_types += 1
        else:
            result.updated_delivery_types += 1

    for item in _merge_default_attack_scenarios(bundle.attack_scenarios):
        row, created = _upsert_attack_scenario(session, item)
        scenario_rows[item.code] = row
        if created:
            result.created_attack_scenarios += 1
        else:
            result.updated_attack_scenarios += 1

    for item in bundle.asset_types:
        _, created = _upsert_asset_type(session, item)
        if created:
            result.created_asset_types += 1
        else:
            result.updated_asset_types += 1

    for item in bundle.risk_categories:
        row, created = _upsert_risk_category(session, item)
        category_rows[item.code] = row
        if created:
            result.created_categories += 1
        else:
            result.updated_categories += 1

    for item in bundle.risk_subtypes:
        category = category_rows.get(item.category_code)
        if category is None:
            raise ImportValidationError(
                f"risk_subtypes.json: category_code={item.category_code} 未定义"
            )
        attack_scenario_code = _resolve_attack_scenario_code(
            item.attack_scenario_code, item.category_code
        )
        scenario = scenario_rows.get(attack_scenario_code)
        if scenario is None:
            raise ImportValidationError(
                f"risk_subtypes.json: attack_scenario_code={attack_scenario_code} 未定义"
            )
        _, domain_created = _upsert_attack_scenario_risk_domain(
            session,
            scenario.id,
            category.id,
            item.sort_order or category.sort_order,
        )
        if domain_created:
            result.created_scenario_risk_domains += 1
        else:
            result.updated_scenario_risk_domains += 1
        row, created = _upsert_risk_subtype(
            session, item, category.id, scenario.id
        )
        subtype_rows[item.code] = row
        if created:
            result.created_subtypes += 1
        else:
            result.updated_subtypes += 1

    unknown_display_meta_codes = set(bundle.display_meta_by_code) - set(subtype_rows)
    if unknown_display_meta_codes:
        raise ImportValidationError(
            f"display_meta: 存在未在 risk_subtypes.json 中注册的 subtype_code={sorted(unknown_display_meta_codes)}"
        )

    for item in bundle.risk_subtypes:
        display_meta = bundle.display_meta_by_code.get(
            item.code, DisplayMetaRecord(subtype_code=item.code)
        )
        _, created = _upsert_display_meta(
            session, subtype_rows[item.code].id, display_meta
        )
        if created:
            result.created_display_meta += 1
        else:
            result.updated_display_meta += 1

    session.flush()
    return result


def _upsert_dataset_source(
    session: Session, record: DatasetSourceRecord
) -> tuple[DatasetSource, bool]:
    """按 code 幂等写入数据源字典项。"""
    row = session.execute(
        select(DatasetSource).where(DatasetSource.code == record.code)
    ).scalar_one_or_none()
    if row is None:
        row = DatasetSource(
            code=record.code,
            name=record.name,
            description=record.description,
            is_active=record.is_active,
            translations=dict(record.translations),
        )
        session.add(row)
        session.flush()
        return row, True
    row.name = record.name
    row.description = record.description
    row.is_active = record.is_active
    row.translations = dict(record.translations)
    session.flush()
    return row, False


def _upsert_attack_delivery_type(
    session: Session, record: AttackDeliveryTypeRecord
) -> tuple[AttackDeliveryType, bool]:
    """按 code 幂等写入攻击投递方式字典项。"""
    row = session.execute(
        select(AttackDeliveryType).where(AttackDeliveryType.code == record.code)
    ).scalar_one_or_none()
    if row is None:
        row = AttackDeliveryType(
            code=record.code,
            name=record.name,
            description=record.description,
            is_active=record.is_active,
            translations=dict(record.translations),
        )
        session.add(row)
        session.flush()
        return row, True
    row.name = record.name
    row.description = record.description
    row.is_active = record.is_active
    row.translations = dict(record.translations)
    session.flush()
    return row, False


def _upsert_attack_scenario(
    session: Session, record: AttackScenarioRecord
) -> tuple[AttackScenario, bool]:
    """按 code 幂等写入攻击场景字典项。"""
    row = session.execute(
        select(AttackScenario).where(AttackScenario.code == record.code)
    ).scalar_one_or_none()
    if row is None:
        row = AttackScenario(
            code=record.code,
            name=record.name,
            description=record.description,
            sort_order=record.sort_order,
            is_active=record.is_active,
            translations=dict(record.translations),
        )
        session.add(row)
        session.flush()
        return row, True
    row.name = record.name
    row.description = record.description
    row.sort_order = record.sort_order
    row.is_active = record.is_active
    row.translations = dict(record.translations)
    session.flush()
    return row, False


def _upsert_asset_type(
    session: Session, record: AssetTypeRecord
) -> tuple[AssetType, bool]:
    """按 code 幂等写入资产类型字典项。"""
    row = session.execute(
        select(AssetType).where(AssetType.code == record.code)
    ).scalar_one_or_none()
    if row is None:
        row = AssetType(
            code=record.code,
            name=record.name,
            description=record.description,
            is_active=record.is_active,
            translations=dict(record.translations),
        )
        session.add(row)
        session.flush()
        return row, True
    row.name = record.name
    row.description = record.description
    row.is_active = record.is_active
    row.translations = dict(record.translations)
    session.flush()
    return row, False


def _upsert_attack_scenario_risk_domain(
    session: Session,
    attack_scenario_id: int,
    risk_category_id: int,
    sort_order: int | None,
) -> tuple[AttackScenarioRiskDomain, bool]:
    """按攻击场景和风险域幂等写入展示关联。"""
    row = session.execute(
        select(AttackScenarioRiskDomain).where(
            AttackScenarioRiskDomain.attack_scenario_id == attack_scenario_id,
            AttackScenarioRiskDomain.risk_category_id == risk_category_id,
        )
    ).scalar_one_or_none()
    if row is None:
        row = AttackScenarioRiskDomain(
            attack_scenario_id=attack_scenario_id,
            risk_category_id=risk_category_id,
            sort_order=sort_order,
            is_active=True,
        )
        session.add(row)
        session.flush()
        return row, True
    row.sort_order = sort_order
    row.is_active = True
    session.flush()
    return row, False


def _upsert_risk_category(
    session: Session, record: RiskCategoryRecord
) -> tuple[RiskCategory, bool]:
    """按 code 幂等写入风险大类字典项。"""
    row = session.execute(
        select(RiskCategory).where(RiskCategory.code == record.code)
    ).scalar_one_or_none()
    if row is None:
        row = RiskCategory(
            code=record.code,
            name=record.name,
            meaning=record.meaning,
            description=record.description,
            sort_order=record.sort_order,
            is_active=record.is_active,
            translations=dict(record.translations),
        )
        session.add(row)
        session.flush()
        return row, True
    row.name = record.name
    row.meaning = record.meaning
    row.description = record.description
    row.sort_order = record.sort_order
    row.is_active = record.is_active
    row.translations = dict(record.translations)
    session.flush()
    return row, False


def _upsert_risk_subtype(
    session: Session,
    record: RiskSubtypeRecord,
    category_id: int,
    attack_scenario_id: int,
) -> tuple[RiskSubtype, bool]:
    """按 code 幂等写入风险子类字典项。"""
    row = session.execute(
        select(RiskSubtype).where(RiskSubtype.code == record.code)
    ).scalar_one_or_none()
    if row is None:
        row = RiskSubtype(
            category_id=category_id,
            attack_scenario_id=attack_scenario_id,
            code=record.code,
            name=record.name,
            sort_order=record.sort_order,
            is_active=record.is_active,
            translations=dict(record.translations),
        )
        session.add(row)
        session.flush()
        return row, True
    row.category_id = category_id
    row.attack_scenario_id = attack_scenario_id
    row.name = record.name
    row.sort_order = record.sort_order
    row.is_active = record.is_active
    row.translations = dict(record.translations)
    session.flush()
    return row, False


def _upsert_display_meta(
    session: Session,
    subtype_id: int,
    record: DisplayMetaRecord,
) -> tuple[RiskSubtypeDisplayMeta, bool]:
    """按子类主键幂等写入展示元数据。"""
    row = session.execute(
        select(RiskSubtypeDisplayMeta).where(
            RiskSubtypeDisplayMeta.subtype_id == subtype_id
        )
    ).scalar_one_or_none()
    if row is None:
        row = RiskSubtypeDisplayMeta(
            subtype_id=subtype_id,
            short_description=record.short_description,
            full_description=record.full_description,
            highlights=list(record.highlights),
            scenarios=list(record.scenarios),
            resources=list(record.resources),
            media=list(record.media),
            translations=dict(record.translations),
        )
        session.add(row)
        session.flush()
        return row, True
    row.short_description = record.short_description
    row.full_description = record.full_description
    row.highlights = list(record.highlights)
    row.scenarios = list(record.scenarios)
    row.resources = list(record.resources)
    row.media = list(record.media)
    row.translations = dict(record.translations)
    session.flush()
    return row, False


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    """读取并校验顶层为数组的 JSON 文件。"""
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ImportValidationError(f"{path}: 顶层必须是数组")
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ImportValidationError(f"{path}: 第 {index} 项必须是对象")
    return cast(list[dict[str, Any]], payload)


def _load_json_object(path: Path) -> dict[str, Any]:
    """读取并校验顶层为对象的 JSON 文件。"""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ImportValidationError(f"{path}: 顶层必须是对象")
    return cast(dict[str, Any], payload)


def _write_json(path: Path, payload: object) -> None:
    """以统一格式写出 JSON 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
