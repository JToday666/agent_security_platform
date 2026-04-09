"""评测任务模块数据访问层。"""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark_run import RunDataset, RunReport, TestRun


class EvaluationRepository:
    """封装评测任务查询与状态持久化操作。"""

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

    async def load_related_for_runs(self, run_ids: list[int]) -> tuple[dict[int, list[RunDataset]], dict[int, RunReport]]:
        if not run_ids:
            return {}, {}

        dataset_rows = list(
            (
                await self.db.execute(
                    select(RunDataset)
                    .where(RunDataset.run_id.in_(run_ids))
                    .order_by(RunDataset.run_id.asc(), RunDataset.order_no.asc(), RunDataset.id.asc())
                )
            ).scalars()
        )
        datasets_by_run: dict[int, list[RunDataset]] = defaultdict(list)
        for dataset in dataset_rows:
            datasets_by_run[dataset.run_id].append(dataset)

        report_rows = list(
            (
                await self.db.execute(select(RunReport).where(RunReport.run_id.in_(run_ids)))
            ).scalars()
        )
        reports_by_run = {report.run_id: report for report in report_rows}
        return dict(datasets_by_run), reports_by_run

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def refresh(self, entity) -> None:
        await self.db.refresh(entity)
