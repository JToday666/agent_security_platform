"""评测任务模块数据访问层。"""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark_run import RunDataset, RunReport, TestRun


class EvaluationRepository:
    """封装评测任务查询与状态持久化操作。"""

    def __init__(self, db: AsyncSession) -> None:
        """绑定评测任务查询链路共用的异步数据库会话。"""
        self.db = db

    async def list_runs_for_user(self, user_id: int) -> list[TestRun]:
        """按用户查询其名下的评测任务列表。"""
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
        """按对外公开编号查询单个评测任务。"""
        return (
            await self.db.execute(select(TestRun).where(TestRun.public_id == public_id))
        ).scalar_one_or_none()

    async def load_run_datasets(self, run_id: int) -> list[RunDataset]:
        """加载评测任务关联的数据集快照列表。"""
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
        """加载评测任务的最终报告记录。"""
        return (
            await self.db.execute(select(RunReport).where(RunReport.run_id == run_id))
        ).scalar_one_or_none()

    async def load_related_for_runs(self, run_ids: list[int]) -> tuple[dict[int, list[RunDataset]], dict[int, RunReport]]:
        """批量加载列表页所需的数据集快照与报告摘要。"""
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
        """提交评测任务相关事务。"""
        await self.db.commit()

    async def rollback(self) -> None:
        """回滚评测任务相关事务。"""
        await self.db.rollback()

    async def refresh(self, entity) -> None:
        """刷新指定实体的数据库状态。"""
        await self.db.refresh(entity)
