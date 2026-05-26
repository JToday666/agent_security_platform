"""数据集模块服务，负责组装评测项目录与详情。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, cast

from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.schemas import (
    DatasetCatalogResponse,
    DatasetCategoryInfo,
    DatasetDetailResponse,
    DatasetDistributionItem,
    DatasetSampleProfile,
)
from app.platform.errors import NotFoundError
from app.platform.i18n import DEFAULT_LOCALE, get_current_locale, translate

TranslationMap = dict[str, dict[int, dict[str, Any]]]
TranslationMapLoader = Callable[[str, list[int], list[int]], Awaitable[TranslationMap]]

UNASSIGNED_ASSET_CODE = "__unassigned__"
UNASSIGNED_ASSET_MESSAGE_KEY = "datasets.sample_profile.asset_unassigned"
DIFFICULTY_BUCKETS: tuple[tuple[str, float, float], ...] = (
    ("0.0-0.2", 0.0, 0.2),
    ("0.2-0.4", 0.2, 0.4),
    ("0.4-0.6", 0.4, 0.6),
    ("0.6-0.8", 0.6, 0.8),
    ("0.8-1.0", 0.8, 1.0),
)


def latest_datetime(*values: datetime | None) -> datetime:
    """返回一组时间中最新的值。"""
    normalized = [value for value in values if value is not None]
    return max(normalized) if normalized else datetime.now(timezone.utc)


def to_zulu(value: datetime) -> str:
    """将时间转换为接口使用的 UTC 字符串。"""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _translated_value(
    translations: dict[int, dict[str, Any]], entity_id: int, field: str, fallback: Any
) -> Any:
    value = translations.get(entity_id, {}).get(field)
    return fallback if value in (None, "") else value


def _translated_list(
    translations: dict[int, dict[str, Any]],
    entity_id: int,
    field: str,
    fallback: list[Any],
) -> list[Any]:
    value = translations.get(entity_id, {}).get(field)
    return list(fallback if value in (None, []) else value)


def _translated_resources(
    translations: dict[int, dict[str, Any]],
    entity_id: int,
    fallback: list[dict[str, object]],
) -> list[dict[str, object]]:
    value = translations.get(entity_id, {}).get("resources")
    return [dict(item) for item in (fallback if value in (None, []) else value)]


def _translated_media(
    translations: dict[int, dict[str, Any]],
    entity_id: int,
    fallback: list[dict[str, object]],
) -> list[dict[str, object]]:
    value = translations.get(entity_id, {}).get("media")
    return [dict(item) for item in (fallback if value in (None, []) else value)]


def _row_value(row: Any, key: str, fallback: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, fallback)
    if hasattr(row, "_mapping"):
        return row._mapping.get(key, fallback)
    return getattr(row, key, fallback)


def _translated_row_label(row: Any, prefix: str, fallback: Any) -> str:
    translations = _row_value(row, f"{prefix}_translations", {})
    if isinstance(translations, dict):
        locale_translations = translations.get(get_current_locale())
        if isinstance(locale_translations, dict):
            label = locale_translations.get("name")
            if label not in (None, ""):
                return str(label).strip()
    return str(fallback or "").strip()


def _rounded_ratio(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total, 4)


def _to_float(value: Any) -> float:
    parsed = float(value)
    return parsed if parsed == parsed else 0.0


def _build_distribution_item(
    code: str,
    label: str,
    count: int,
    total: int,
) -> DatasetDistributionItem:
    return DatasetDistributionItem(
        code=code,
        label=label,
        count=count,
        ratio=_rounded_ratio(count, total),
    )


def _increment_distribution(
    accumulator: dict[str, dict[str, Any]],
    code: Any,
    label: Any,
    *,
    fallback_code: str | None = None,
    fallback_label: str | None = None,
) -> None:
    normalized_code = str(code or fallback_code or "").strip()
    normalized_label = str(label or fallback_label or normalized_code).strip()
    if not normalized_code:
        return
    entry = accumulator.setdefault(
        normalized_code, {"code": normalized_code, "label": normalized_label, "count": 0}
    )
    entry["count"] += 1


def _finalize_distribution(
    accumulator: dict[str, dict[str, Any]],
    total: int,
    *,
    limit: int | None = None,
) -> list[DatasetDistributionItem]:
    items = [
        _build_distribution_item(
            str(item["code"]), str(item["label"]), int(item["count"]), total
        )
        for item in accumulator.values()
    ]
    sorted_items = sorted(items, key=lambda item: (-item.count, item.label, item.code))
    return sorted_items[:limit] if limit is not None else sorted_items


def _build_difficulty_buckets(
    rows: list[Any],
    total: int,
) -> list[DatasetDistributionItem]:
    scores = [
        min(1.0, max(0.0, _to_float(_row_value(row, "difficulty_score", 0))))
        for row in rows
    ]
    bucket_counts = {code: 0 for code, _lower, _upper in DIFFICULTY_BUCKETS}
    for score in scores:
        for index, (code, lower, upper) in enumerate(DIFFICULTY_BUCKETS):
            is_last = index == len(DIFFICULTY_BUCKETS) - 1
            in_bucket = (
                (lower <= score <= upper) if is_last else (lower <= score < upper)
            )
            if in_bucket:
                bucket_counts[code] += 1
                break

    return [
        _build_distribution_item(code, code, bucket_counts[code], total)
        for code, _lower, _upper in DIFFICULTY_BUCKETS
    ]


def _build_sample_profile(rows: list[Any], total_samples: int) -> DatasetSampleProfile:
    delivery_distribution: dict[str, dict[str, Any]] = {}
    asset_distribution: dict[str, dict[str, Any]] = {}
    total = max(0, int(total_samples))

    for row in rows:
        _increment_distribution(
            delivery_distribution,
            _row_value(row, "delivery_code"),
            _translated_row_label(row, "delivery", _row_value(row, "delivery_name")),
        )
        _increment_distribution(
            asset_distribution,
            _row_value(row, "asset_type_code"),
            _translated_row_label(row, "asset_type", _row_value(row, "asset_type_name")),
            fallback_code=UNASSIGNED_ASSET_CODE,
            fallback_label=translate(UNASSIGNED_ASSET_MESSAGE_KEY),
        )

    return DatasetSampleProfile(
        delivery_distribution=_finalize_distribution(delivery_distribution, total),
        asset_type_top=_finalize_distribution(asset_distribution, total, limit=5),
        difficulty_buckets=_build_difficulty_buckets(rows, total),
    )


class DatasetService:
    """封装数据集查询相关业务能力。"""

    def __init__(self, repository: DatasetRepository) -> None:
        """绑定目录与详情查询共用的数据仓储。"""
        self.repository = repository

    async def get_catalog(self) -> DatasetCatalogResponse:
        """返回前端展示用的数据集目录。"""
        rows = await self.repository.get_catalog_rows()
        translation_maps = await self._load_translation_maps(rows)
        category_translations = translation_maps["categories"]
        subtype_translations = translation_maps["subtypes"]
        display_meta_translations = translation_maps["display_meta"]
        categories: list[dict[str, Any]] = []
        category_map: dict[int, dict[str, Any]] = {}
        version_candidates: list[datetime] = []

        for category, subtype, display_meta, sample_count, sample_updated_at in rows:
            if not sample_count:
                continue

            updated_at = latest_datetime(
                category.updated_at,
                getattr(display_meta, "updated_at", None),
                sample_updated_at,
            )
            version_candidates.append(updated_at)

            category_item = category_map.get(category.id)
            if category_item is None:
                category_item = {
                    "categoryId": category.code,
                    "name": _translated_value(
                        category_translations, category.id, "name", category.name
                    ),
                    "meaning": _translated_value(
                        category_translations, category.id, "meaning", category.meaning
                    ),
                    "description": _translated_value(
                        category_translations,
                        category.id,
                        "description",
                        category.description,
                    ),
                    "sort": category.sort_order,
                    "enabled": category.is_active,
                    "subcategoryCount": 0,
                    "subcategories": [],
                }
                category_map[category.id] = category_item
                categories.append(category_item)

            category_item["subcategories"].append(
                {
                    "datasetId": subtype.code,
                    "name": _translated_value(
                        subtype_translations, subtype.id, "name", subtype.name
                    ),
                    "shortDescription": _translated_value(
                        display_meta_translations,
                        subtype.id,
                        "short_description",
                        getattr(display_meta, "short_description", None),
                    ),
                    "sampleCount": int(sample_count),
                    "updatedAt": to_zulu(updated_at),
                    "enabled": subtype.is_active,
                }
            )
            category_item["subcategoryCount"] += 1

        if not version_candidates:
            version_candidates = [
                row[0].updated_at for row in rows if row[0] is not None
            ]

        return DatasetCatalogResponse.model_validate(
            {
                "catalogVersion": to_zulu(
                    max(version_candidates)
                    if version_candidates
                    else datetime.now(timezone.utc)
                ),
                "categoryCount": len(categories),
                "subcategoryCount": sum(
                    category["subcategoryCount"] for category in categories
                ),
                "categories": categories,
            }
        )

    async def get_detail(self, dataset_id: str) -> DatasetDetailResponse:
        """返回单个数据集的详情信息。"""
        row = await self.repository.get_detail_row(dataset_id)
        if row is None or not row.sample_count:
            raise NotFoundError(
                "评测项不存在。", message_key="errors.datasets.not_found"
            )

        category, subtype, display_meta, sample_count, sample_updated_at = row
        translation_maps = await self._load_translation_maps([row])
        category_translations = translation_maps["categories"]
        subtype_translations = translation_maps["subtypes"]
        display_meta_translations = translation_maps["display_meta"]
        updated_at = latest_datetime(
            category.updated_at,
            getattr(display_meta, "updated_at", None),
            sample_updated_at,
        )
        sample_rows_loader = getattr(self.repository, "get_detail_sample_rows", None)
        sample_rows = (
            await sample_rows_loader(subtype.code)
            if callable(sample_rows_loader)
            else []
        )
        return DatasetDetailResponse(
            dataset_id=subtype.code,
            name=_translated_value(
                subtype_translations, subtype.id, "name", subtype.name
            ),
            category=DatasetCategoryInfo(
                category_id=category.code,
                name=_translated_value(
                    category_translations, category.id, "name", category.name
                ),
                meaning=_translated_value(
                    category_translations, category.id, "meaning", category.meaning
                ),
            ),
            short_description=_translated_value(
                display_meta_translations,
                subtype.id,
                "short_description",
                getattr(display_meta, "short_description", None),
            ),
            full_description=_translated_value(
                display_meta_translations,
                subtype.id,
                "full_description",
                getattr(display_meta, "full_description", None),
            ),
            sample_count=int(sample_count),
            updated_at=to_zulu(updated_at),
            highlights=_translated_list(
                display_meta_translations,
                subtype.id,
                "highlights",
                list(getattr(display_meta, "highlights", []) or []),
            ),
            scenarios=_translated_list(
                display_meta_translations,
                subtype.id,
                "scenarios",
                list(getattr(display_meta, "scenarios", []) or []),
            ),
            resources=_translated_resources(
                display_meta_translations,
                subtype.id,
                list(getattr(display_meta, "resources", []) or []),
            ),
            media=_translated_media(
                display_meta_translations,
                subtype.id,
                list(getattr(display_meta, "media", []) or []),
            ),
            sample_profile=_build_sample_profile(sample_rows, int(sample_count)),
        )

    async def _load_translation_maps(self, rows) -> TranslationMap:
        """Load locale-specific metadata translations, if the repository supports them."""
        empty: TranslationMap = {
            "categories": {},
            "subtypes": {},
            "display_meta": {},
        }
        locale = get_current_locale()
        loader = getattr(self.repository, "load_translation_maps", None)
        if locale == DEFAULT_LOCALE or not callable(loader):
            return empty
        category_ids: list[int] = []
        subtype_ids: list[int] = []
        for category, subtype, _display_meta, _sample_count, _sample_updated_at in rows:
            category_ids.append(category.id)
            subtype_ids.append(subtype.id)
        typed_loader = cast(TranslationMapLoader, loader)
        return await typed_loader(
            locale,
            sorted(set(category_ids)),
            sorted(set(subtype_ids)),
        )
