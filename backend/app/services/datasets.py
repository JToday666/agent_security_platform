from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.response import fail
from app.models.benchmark import BenchmarkSample, RiskCategory, RiskSubtype, RiskSubtypeDisplayMeta

class DatasetService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_catalog(self) -> dict[str, object]:
        stmt = (
            select(
                RiskCategory,
                RiskSubtype,
                RiskSubtypeDisplayMeta,
                func.count(BenchmarkSample.id).label("sample_count"),
                func.max(BenchmarkSample.updated_at).label("sample_updated_at"),
            )
            .join(RiskSubtype, RiskSubtype.category_id == RiskCategory.id)
            .outerjoin(RiskSubtypeDisplayMeta, RiskSubtypeDisplayMeta.subtype_id == RiskSubtype.id)
            .outerjoin(
                BenchmarkSample,
                and_(
                    BenchmarkSample.risk_subtype_id == RiskSubtype.id,
                    BenchmarkSample.is_active.is_(True),
                ),
            )
            .where(RiskCategory.is_active.is_(True), RiskSubtype.is_active.is_(True))
            .group_by(RiskCategory.id, RiskSubtype.id, RiskSubtypeDisplayMeta.subtype_id)
            .order_by(RiskCategory.sort_order.asc().nullslast(), RiskCategory.id.asc(), RiskSubtype.sort_order.asc().nullslast(), RiskSubtype.id.asc())
        )

        rows = (await self.db.execute(stmt)).all()
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
            version_candidates = [
                row[0].updated_at
                for row in rows
                if row[0] is not None
            ]

        catalog_version = to_zulu(max(version_candidates) if version_candidates else datetime.now(timezone.utc))
        subcategory_count = sum(category["subcategoryCount"] for category in categories)
        return {
            "catalogVersion": catalog_version,
            "categoryCount": len(categories),
            "subcategoryCount": subcategory_count,
            "categories": categories,
        }

    async def get_detail(self, dataset_id: str) -> dict[str, object]:
        stmt = (
            select(
                RiskCategory,
                RiskSubtype,
                RiskSubtypeDisplayMeta,
                func.count(BenchmarkSample.id).label("sample_count"),
                func.max(BenchmarkSample.updated_at).label("sample_updated_at"),
            )
            .join(RiskSubtype, RiskSubtype.category_id == RiskCategory.id)
            .outerjoin(RiskSubtypeDisplayMeta, RiskSubtypeDisplayMeta.subtype_id == RiskSubtype.id)
            .outerjoin(
                BenchmarkSample,
                and_(
                    BenchmarkSample.risk_subtype_id == RiskSubtype.id,
                    BenchmarkSample.is_active.is_(True),
                ),
            )
            .where(
                RiskCategory.is_active.is_(True),
                RiskSubtype.is_active.is_(True),
                RiskSubtype.code == dataset_id,
            )
            .group_by(RiskCategory.id, RiskSubtype.id, RiskSubtypeDisplayMeta.subtype_id)
        )
        row = (await self.db.execute(stmt)).one_or_none()
        if row is None or not row.sample_count:
            raise fail(404, 40400, "评测项不存在。")

        category, subtype, display_meta, sample_count, sample_updated_at = row
        updated_at = latest_datetime(
            category.updated_at,
            getattr(display_meta, "updated_at", None),
            sample_updated_at,
        )
        return {
            "datasetId": subtype.code,
            "name": subtype.name,
            "category": {
                "categoryId": category.code,
                "name": category.name,
                "meaning": category.meaning,
            },
            "shortDescription": getattr(display_meta, "short_description", None),
            "fullDescription": getattr(display_meta, "full_description", None),
            "sampleCount": int(sample_count),
            "updatedAt": to_zulu(updated_at),
            "highlights": list(getattr(display_meta, "highlights", []) or []),
            "scenarios": list(getattr(display_meta, "scenarios", []) or []),
            "resources": list(getattr(display_meta, "resources", []) or []),
            "media": list(getattr(display_meta, "media", []) or []),
        }


def latest_datetime(*values: datetime | None) -> datetime:
    normalized = [value for value in values if value is not None]
    return max(normalized) if normalized else datetime.now(timezone.utc)


def to_zulu(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
