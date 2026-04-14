"""版本化数据集元数据的 JSON 读写、同步与入库逻辑。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benchmark import (
    AssetType,
    AttackDeliveryType,
    DatasetSource,
    RiskCategory,
    RiskSubtype,
    RiskSubtypeDisplayMeta,
)
from app.modules.datasets.db_support import sync_pk_sequence
from app.modules.datasets.importer import (
    ImportValidationError,
    build_sample_import_plan,
    default_category_name,
    default_category_sort_order,
    default_subtype_name,
    default_subtype_sort_order,
    humanize_code,
)


@dataclass(slots=True)
class DatasetSourceRecord:
    code: str
    name: str
    description: str | None = None
    is_active: bool = True


@dataclass(slots=True)
class AttackDeliveryTypeRecord:
    code: str
    name: str
    description: str | None = None
    is_active: bool = True


@dataclass(slots=True)
class AssetTypeRecord:
    code: str
    name: str
    description: str | None = None
    is_active: bool = True


@dataclass(slots=True)
class RiskCategoryRecord:
    code: str
    name: str
    meaning: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool = True


@dataclass(slots=True)
class RiskSubtypeRecord:
    code: str
    category_code: str
    name: str
    sort_order: int | None = None
    is_active: bool = True


@dataclass(slots=True)
class DisplayMetaRecord:
    subtype_code: str
    short_description: str | None = None
    full_description: str | None = None
    highlights: list[str] = field(default_factory=list)
    scenarios: list[str] = field(default_factory=list)
    resources: list[dict[str, object]] = field(default_factory=list)
    media: list[dict[str, object]] = field(default_factory=list)


@dataclass(slots=True)
class MetadataBundle:
    dataset_sources: list[DatasetSourceRecord] = field(default_factory=list)
    attack_delivery_types: list[AttackDeliveryTypeRecord] = field(default_factory=list)
    asset_types: list[AssetTypeRecord] = field(default_factory=list)
    risk_categories: list[RiskCategoryRecord] = field(default_factory=list)
    risk_subtypes: list[RiskSubtypeRecord] = field(default_factory=list)
    display_meta_by_code: dict[str, DisplayMetaRecord] = field(default_factory=dict)


@dataclass(slots=True)
class MetadataImportResult:
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


def load_metadata_bundle(registry_root: Path) -> MetadataBundle:
    """从 registry/display_meta 目录读取元数据。"""
    root = registry_root.resolve()
    bundle = MetadataBundle(
        dataset_sources=[DatasetSourceRecord(**item) for item in _load_json_list(root / "registry" / "dataset_sources.json")],
        attack_delivery_types=[
            AttackDeliveryTypeRecord(**item) for item in _load_json_list(root / "registry" / "attack_delivery_types.json")
        ],
        asset_types=[AssetTypeRecord(**item) for item in _load_json_list(root / "registry" / "asset_types.json")],
        risk_categories=[RiskCategoryRecord(**item) for item in _load_json_list(root / "registry" / "risk_categories.json")],
        risk_subtypes=[RiskSubtypeRecord(**item) for item in _load_json_list(root / "registry" / "risk_subtypes.json")],
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
    (root / "workbook").mkdir(parents=True, exist_ok=True)

    _write_json(root / "registry" / "dataset_sources.json", [asdict(item) for item in sorted(bundle.dataset_sources, key=lambda item: item.code)])
    _write_json(
        root / "registry" / "attack_delivery_types.json",
        [asdict(item) for item in sorted(bundle.attack_delivery_types, key=lambda item: item.code)],
    )
    _write_json(root / "registry" / "asset_types.json", [asdict(item) for item in sorted(bundle.asset_types, key=lambda item: item.code)])
    _write_json(
        root / "registry" / "risk_categories.json",
        [asdict(item) for item in sorted(bundle.risk_categories, key=lambda item: ((item.sort_order or 999), item.code))],
    )
    _write_json(
        root / "registry" / "risk_subtypes.json",
        [asdict(item) for item in sorted(bundle.risk_subtypes, key=lambda item: ((item.sort_order or 999), item.code))],
    )
    for code, record in sorted(bundle.display_meta_by_code.items()):
        _write_json(root / "display_meta" / f"{code}.json", asdict(record))
    write_display_meta_index(root, bundle)


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
            category.sort_order if category and category.sort_order is not None else 999,
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
                "short_description": display_meta.short_description if display_meta else None,
                "path": f"display_meta/{code}.json",
            }
        )
    return index_rows


def sync_registry_from_samples(sample_root: Path, registry_root: Path, mode: str = "auto") -> MetadataBundle:
    """从样本目录补齐 registry 与 display_meta 骨架。"""
    bundle = load_metadata_bundle(registry_root)
    source_by_code = {item.code: item for item in bundle.dataset_sources}
    delivery_by_code = {item.code: item for item in bundle.attack_delivery_types}
    asset_by_code = {item.code: item for item in bundle.asset_types}
    category_by_code = {item.code: item for item in bundle.risk_categories}
    subtype_by_code = {item.code: item for item in bundle.risk_subtypes}
    display_meta_by_code = dict(bundle.display_meta_by_code)

    sample_plan = build_sample_import_plan(sample_root, mode=mode)
    for sample in sample_plan.samples:
        if sample.dataset_source_code not in source_by_code:
            source_by_code[sample.dataset_source_code] = DatasetSourceRecord(
                code=sample.dataset_source_code,
                name=sample.dataset_source_name or humanize_code(sample.dataset_source_code),
            )
        if sample.attack_delivery_type_code not in delivery_by_code:
            delivery_by_code[sample.attack_delivery_type_code] = AttackDeliveryTypeRecord(
                code=sample.attack_delivery_type_code,
                name=sample.attack_delivery_type_name or humanize_code(sample.attack_delivery_type_code),
            )
        if sample.asset_type_code and sample.asset_type_code not in asset_by_code:
            asset_by_code[sample.asset_type_code] = AssetTypeRecord(
                code=sample.asset_type_code,
                name=sample.asset_type_name or humanize_code(sample.asset_type_code),
            )
        if sample.risk_category_code not in category_by_code:
            category_by_code[sample.risk_category_code] = RiskCategoryRecord(
                code=sample.risk_category_code,
                name=sample.risk_category_name or default_category_name(sample.risk_category_code),
                sort_order=sample.risk_category_sort_order or default_category_sort_order(sample.risk_category_code),
            )
        if sample.risk_subtype_code not in subtype_by_code:
            subtype_by_code[sample.risk_subtype_code] = RiskSubtypeRecord(
                code=sample.risk_subtype_code,
                category_code=sample.risk_category_code,
                name=sample.risk_subtype_name or default_subtype_name(sample.risk_subtype_code),
                sort_order=sample.risk_subtype_sort_order or default_subtype_sort_order(sample.risk_subtype_code),
            )
        if sample.risk_subtype_code not in display_meta_by_code:
            display_meta_by_code[sample.risk_subtype_code] = DisplayMetaRecord(subtype_code=sample.risk_subtype_code)

    merged_bundle = MetadataBundle(
        dataset_sources=list(source_by_code.values()),
        attack_delivery_types=list(delivery_by_code.values()),
        asset_types=list(asset_by_code.values()),
        risk_categories=list(category_by_code.values()),
        risk_subtypes=list(subtype_by_code.values()),
        display_meta_by_code=display_meta_by_code,
    )
    write_metadata_bundle(registry_root, merged_bundle)
    return merged_bundle


def build_metadata_bundle_from_database(session: Session) -> MetadataBundle:
    """从数据库导出当前元数据。"""
    categories = session.execute(select(RiskCategory).order_by(RiskCategory.sort_order.asc().nullslast(), RiskCategory.code.asc())).scalars().all()
    subtypes = session.execute(select(RiskSubtype).order_by(RiskSubtype.sort_order.asc().nullslast(), RiskSubtype.code.asc())).scalars().all()
    category_code_by_id = {item.id: item.code for item in categories}

    bundle = MetadataBundle(
        dataset_sources=[
            DatasetSourceRecord(
                code=item.code,
                name=item.name,
                description=item.description,
                is_active=item.is_active,
            )
            for item in session.execute(select(DatasetSource).order_by(DatasetSource.code.asc())).scalars()
        ],
        attack_delivery_types=[
            AttackDeliveryTypeRecord(
                code=item.code,
                name=item.name,
                description=item.description,
                is_active=item.is_active,
            )
            for item in session.execute(select(AttackDeliveryType).order_by(AttackDeliveryType.code.asc())).scalars()
        ],
        asset_types=[
            AssetTypeRecord(
                code=item.code,
                name=item.name,
                description=item.description,
                is_active=item.is_active,
            )
            for item in session.execute(select(AssetType).order_by(AssetType.code.asc())).scalars()
        ],
        risk_categories=[
            RiskCategoryRecord(
                code=item.code,
                name=item.name,
                meaning=item.meaning,
                description=item.description,
                sort_order=item.sort_order,
                is_active=item.is_active,
            )
            for item in categories
        ],
        risk_subtypes=[
            RiskSubtypeRecord(
                code=item.code,
                category_code=category_code_by_id[item.category_id],
                name=item.name,
                sort_order=item.sort_order,
                is_active=item.is_active,
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
        )

    return bundle


def apply_metadata_bundle(session: Session, bundle: MetadataBundle) -> MetadataImportResult:
    """将 JSON 元数据幂等写入数据库。"""
    for table_name in ("dataset_sources", "attack_delivery_types", "asset_types", "risk_categories", "risk_subtypes"):
        sync_pk_sequence(session, table_name)

    result = MetadataImportResult()
    category_rows: dict[str, RiskCategory] = {}
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
            raise ImportValidationError(f"risk_subtypes.json: category_code={item.category_code} 未定义")
        row, created = _upsert_risk_subtype(session, item, category.id)
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
        display_meta = bundle.display_meta_by_code.get(item.code, DisplayMetaRecord(subtype_code=item.code))
        _, created = _upsert_display_meta(session, subtype_rows[item.code].id, display_meta)
        if created:
            result.created_display_meta += 1
        else:
            result.updated_display_meta += 1

    session.flush()
    return result


def _upsert_dataset_source(session: Session, record: DatasetSourceRecord) -> tuple[DatasetSource, bool]:
    row = session.execute(select(DatasetSource).where(DatasetSource.code == record.code)).scalar_one_or_none()
    if row is None:
        row = DatasetSource(
            code=record.code,
            name=record.name,
            description=record.description,
            is_active=record.is_active,
        )
        session.add(row)
        session.flush()
        return row, True
    row.name = record.name
    row.description = record.description
    row.is_active = record.is_active
    session.flush()
    return row, False


def _upsert_attack_delivery_type(session: Session, record: AttackDeliveryTypeRecord) -> tuple[AttackDeliveryType, bool]:
    row = session.execute(select(AttackDeliveryType).where(AttackDeliveryType.code == record.code)).scalar_one_or_none()
    if row is None:
        row = AttackDeliveryType(
            code=record.code,
            name=record.name,
            description=record.description,
            is_active=record.is_active,
        )
        session.add(row)
        session.flush()
        return row, True
    row.name = record.name
    row.description = record.description
    row.is_active = record.is_active
    session.flush()
    return row, False


def _upsert_asset_type(session: Session, record: AssetTypeRecord) -> tuple[AssetType, bool]:
    row = session.execute(select(AssetType).where(AssetType.code == record.code)).scalar_one_or_none()
    if row is None:
        row = AssetType(
            code=record.code,
            name=record.name,
            description=record.description,
            is_active=record.is_active,
        )
        session.add(row)
        session.flush()
        return row, True
    row.name = record.name
    row.description = record.description
    row.is_active = record.is_active
    session.flush()
    return row, False


def _upsert_risk_category(session: Session, record: RiskCategoryRecord) -> tuple[RiskCategory, bool]:
    row = session.execute(select(RiskCategory).where(RiskCategory.code == record.code)).scalar_one_or_none()
    if row is None:
        row = RiskCategory(
            code=record.code,
            name=record.name,
            meaning=record.meaning,
            description=record.description,
            sort_order=record.sort_order,
            is_active=record.is_active,
        )
        session.add(row)
        session.flush()
        return row, True
    row.name = record.name
    row.meaning = record.meaning
    row.description = record.description
    row.sort_order = record.sort_order
    row.is_active = record.is_active
    session.flush()
    return row, False


def _upsert_risk_subtype(session: Session, record: RiskSubtypeRecord, category_id: int) -> tuple[RiskSubtype, bool]:
    row = session.execute(select(RiskSubtype).where(RiskSubtype.code == record.code)).scalar_one_or_none()
    if row is None:
        row = RiskSubtype(
            category_id=category_id,
            code=record.code,
            name=record.name,
            sort_order=record.sort_order,
            is_active=record.is_active,
        )
        session.add(row)
        session.flush()
        return row, True
    row.category_id = category_id
    row.name = record.name
    row.sort_order = record.sort_order
    row.is_active = record.is_active
    session.flush()
    return row, False


def _upsert_display_meta(
    session: Session,
    subtype_id: int,
    record: DisplayMetaRecord,
) -> tuple[RiskSubtypeDisplayMeta, bool]:
    row = session.execute(
        select(RiskSubtypeDisplayMeta).where(RiskSubtypeDisplayMeta.subtype_id == subtype_id)
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
    session.flush()
    return row, False


def _load_json_list(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ImportValidationError(f"{path}: 顶层必须是数组")
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ImportValidationError(f"{path}: 第 {index} 项必须是对象")
    return payload


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ImportValidationError(f"{path}: 顶层必须是对象")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
