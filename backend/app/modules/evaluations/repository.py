from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark_run import RunDataset, RunReport, TestRun


class EvaluationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_runs_for_user(self, user_id: int) -> list[TestRun]:
        return list(
            (
                await self.db.execute(
                    select(TestRun)
                    .where(TestRun.user_id == user_id)
                    .order_by(TestRun.created_at.desc(), TestRun.id.desc())
                )
            ).scalars()
        )

    async def get_run_by_public_id(self, public_id: str) -> TestRun | None:
        return (
            await self.db.execute(select(TestRun).where(TestRun.public_id == public_id))
        ).scalar_one_or_none()

    async def load_run_datasets(self, run_id: int) -> list[RunDataset]:
        return list(
            (
                await self.db.execute(
                    select(RunDataset)
                    .where(RunDataset.run_id == run_id)
                    .order_by(RunDataset.order_no.asc(), RunDataset.id.asc())
                )
            ).scalars()
        )

    async def load_run_report(self, run_id: int) -> RunReport | None:
        return (
            await self.db.execute(select(RunReport).where(RunReport.run_id == run_id))
        ).scalar_one_or_none()

    async def commit(self) -> None:
        await self.db.commit()

    async def refresh(self, entity) -> None:
        await self.db.refresh(entity)
