"""提交模块数据访问层。"""

from collections import defaultdict

from sqlalchemy import and_, case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import RunDataset, RunSample, SampleExecution, TestRun


class SubmissionRepository:
    """封装评测任务创建所需的数据库操作。"""

    def __init__(self, db: AsyncSession) -> None:
        """绑定评测任务创建链路共用的异步数据库会话。"""
        self.db = db

    async def get_existing_run(self, user_id: int, request_id: str) -> TestRun | None:
        """按用户与请求编号查询已存在的幂等任务。"""
        return (
            await self.db.execute(
                select(TestRun).where(
                    TestRun.user_id == user_id,
                    TestRun.request_id == request_id,
                )
            )
        ).scalar_one_or_none()

    async def resolve_dataset_selection(self, ordered_dataset_ids: list[str], difficulty: float):
        """解析用户选择的数据集，并返回命中的样本与统计结果。"""
        dataset_stmt = (
            select(RiskSubtype.code, RiskSubtype.name)
            .join(
                BenchmarkSample,
                and_(
                    BenchmarkSample.risk_subtype_id == RiskSubtype.id,
                    BenchmarkSample.is_active.is_(True),
                ),
            )
            .where(RiskSubtype.is_active.is_(True), RiskSubtype.code.in_(ordered_dataset_ids))
            .group_by(RiskSubtype.code, RiskSubtype.name)
        )
        dataset_rows = (await self.db.execute(dataset_stmt)).all()
        dataset_names = {code: name for code, name in dataset_rows}

        ordering = case({dataset_id: index for index, dataset_id in enumerate(ordered_dataset_ids)}, value=RiskSubtype.code)
        sample_stmt = (
            select(BenchmarkSample, RiskSubtype.code)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(
                BenchmarkSample.is_active.is_(True),
                RiskSubtype.code.in_(ordered_dataset_ids),
            )
            .order_by(ordering.asc(), BenchmarkSample.id.asc())
        )
        lower = max(0.0, round(difficulty - 0.05, 2))
        upper = min(1.0, round(difficulty + 0.05, 2))
        include_upper = upper == 1.0
        if include_upper:
            sample_stmt = sample_stmt.where(
                BenchmarkSample.difficulty_score >= lower,
                BenchmarkSample.difficulty_score <= upper,
            )
        else:
            sample_stmt = sample_stmt.where(
                BenchmarkSample.difficulty_score >= lower,
                BenchmarkSample.difficulty_score < upper,
            )

        sample_rows = (await self.db.execute(sample_stmt)).all()
        matched_counts: dict[str, int] = defaultdict(int)
        ordered_samples = []
        for sample, dataset_code in sample_rows:
            matched_counts[dataset_code] += 1
            ordered_samples.append(sample)

        return {
            "dataset_names": dataset_names,
            "sample_rows": ordered_samples,
            "matched_counts": {dataset_id: matched_counts.get(dataset_id, 0) for dataset_id in ordered_dataset_ids},
        }

    async def create_run_graph(
        self,
        run: TestRun,
        dataset_ids: list[str],
        dataset_names: dict[str, str],
        matched_counts: dict[str, int],
        sample_rows: list[BenchmarkSample],
    ) -> TestRun:
        """创建任务、数据集快照、样本映射与执行记录整棵图结构。"""
        self.db.add(run)
        await self.db.flush()

        run_datasets: list[RunDataset] = []
        for order_no, dataset_id in enumerate(dataset_ids, start=1):
            run_datasets.append(
                RunDataset(
                    run_id=run.id,
                    dataset_code=dataset_id,
                    dataset_name=dataset_names[dataset_id],
                    order_no=order_no,
                    status="pending",
                    total_samples=matched_counts[dataset_id],
                    completed_samples=0,
                )
            )
        self.db.add_all(run_datasets)

        run_samples: list[RunSample] = []
        for global_order, sample_row in enumerate(sample_rows, start=1):
            run_samples.append(
                RunSample(
                    run_id=run.id,
                    sample_id_ref=sample_row.id,
                    order_no=global_order,
                )
            )
        self.db.add_all(run_samples)
        await self.db.flush()

        self.db.add_all(
            [
                SampleExecution(
                    run_id=run.id,
                    run_sample_id=run_sample.id,
                    sample_id_ref=run_sample.sample_id_ref,
                    status="pending",
                    retry_no=0,
                )
                for run_sample in run_samples
            ]
        )
        await self.db.flush()
        return run

    async def commit(self) -> None:
        """提交提交链路相关事务。"""
        await self.db.commit()

    async def rollback(self) -> None:
        """回滚提交链路相关事务。"""
        await self.db.rollback()

    async def refresh(self, entity) -> None:
        """刷新指定实体的数据库状态。"""
        await self.db.refresh(entity)
