from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import BenchmarkSample, RiskCategory, RiskSubtype, RiskSubtypeDisplayMeta


class DatasetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_catalog_rows(self):
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
            .order_by(
                RiskCategory.sort_order.asc().nullslast(),
                RiskCategory.id.asc(),
                RiskSubtype.sort_order.asc().nullslast(),
                RiskSubtype.id.asc(),
            )
        )
        return (await self.db.execute(stmt)).all()

    async def get_detail_row(self, dataset_id: str):
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
        return (await self.db.execute(stmt)).one_or_none()
