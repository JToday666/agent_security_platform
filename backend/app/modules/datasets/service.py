"""数据集模块服务，负责组装评测项目录与详情。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, cast

from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.schemas import (
    DatasetCatalogResponse,
    DatasetCategoryInfo,
    DatasetDetailResponse,
)
from app.platform.errors import NotFoundError
from app.platform.i18n import DEFAULT_LOCALE, get_current_locale

TranslationMap = dict[str, dict[int, dict[str, Any]]]
TranslationMapLoader = Callable[[str, list[int], list[int]], Awaitable[TranslationMap]]


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
