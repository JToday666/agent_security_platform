"""数据集模块服务，负责组装评测项目录与详情。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.schemas import DatasetCatalogResponse, DatasetCategoryInfo, DatasetDetailResponse
from app.shared.errors import NotFoundError


def latest_datetime(*values: datetime | None) -> datetime:
    """返回一组时间中最新的值。"""
    normalized = [value for value in values if value is not None]
    return max(normalized) if normalized else datetime.now(timezone.utc)


def to_zulu(value: datetime) -> str:
    """将时间转换为接口使用的 UTC 字符串。"""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class DatasetService:
    """封装数据集查询相关业务能力。"""

    def __init__(self, repository: DatasetRepository) -> None:
        self.repository = repository

    async def get_catalog(self) -> DatasetCatalogResponse:
        """返回前端展示用的数据集目录。"""
        rows = await self.repository.get_catalog_rows()
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
                    "name": category.name,
                    "meaning": category.meaning,
                    "description": category.description,
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
                    "name": subtype.name,
                    "shortDescription": getattr(display_meta, "short_description", None),
                    "sampleCount": int(sample_count),
                    "updatedAt": to_zulu(updated_at),
                    "enabled": subtype.is_active,
                }
            )
            category_item["subcategoryCount"] += 1

        if not version_candidates:
            version_candidates = [row[0].updated_at for row in rows if row[0] is not None]

        return DatasetCatalogResponse.model_validate(
            {
                "catalogVersion": to_zulu(max(version_candidates) if version_candidates else datetime.now(timezone.utc)),
                "categoryCount": len(categories),
                "subcategoryCount": sum(category["subcategoryCount"] for category in categories),
                "categories": categories,
            }
        )

    async def get_detail(self, dataset_id: str) -> DatasetDetailResponse:
        """返回单个数据集的详情信息。"""
        row = await self.repository.get_detail_row(dataset_id)
        if row is None or not row.sample_count:
            raise NotFoundError("评测项不存在。")

        category, subtype, display_meta, sample_count, sample_updated_at = row
        updated_at = latest_datetime(
            category.updated_at,
            getattr(display_meta, "updated_at", None),
            sample_updated_at,
        )
        return DatasetDetailResponse(
            dataset_id=subtype.code,
            name=subtype.name,
            category=DatasetCategoryInfo(
                category_id=category.code,
                name=category.name,
                meaning=category.meaning,
            ),
            short_description=getattr(display_meta, "short_description", None),
            full_description=getattr(display_meta, "full_description", None),
            sample_count=int(sample_count),
            updated_at=to_zulu(updated_at),
            highlights=list(getattr(display_meta, "highlights", []) or []),
            scenarios=list(getattr(display_meta, "scenarios", []) or []),
            resources=list(getattr(display_meta, "resources", []) or []),
            media=list(getattr(display_meta, "media", []) or []),
        )
