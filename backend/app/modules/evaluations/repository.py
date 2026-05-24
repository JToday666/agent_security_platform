"""评测任务模块数据访问层。"""

from collections import defaultdict

from sqlalchemy import and_, case, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.agent import Agent
from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import ExecutionSummary, RunDataset, RunReport, TestRun
from app.models.benchmark_run import RunSample, SampleExecution
from app.models.scoring import DifficultyVersion, DifficultyVersionItem, EvaluationScore


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

    async def get_existing_run(self, user_id: int, request_id: str) -> TestRun | None:
        """按用户和幂等请求号查询已有任务。"""
        return (
            await self.db.execute(
                select(TestRun).where(
                    TestRun.user_id == user_id,
                    TestRun.request_id == request_id,
                )
            )
        ).scalar_one_or_none()

    async def get_agent_by_public_id(self, public_id: str) -> Agent | None:
        """按对外 Agent ID 查询 Agent。"""
        return (
            await self.db.execute(select(Agent).where(Agent.public_id == public_id))
        ).scalar_one_or_none()

    async def resolve_dataset_selection(
        self, ordered_dataset_ids: list[str], difficulty: float
    ):
        """解析数据集选择并返回匹配样本。"""
        dataset_stmt = (
            select(RiskSubtype.code, RiskSubtype.name)
            .join(
                BenchmarkSample,
                and_(
                    BenchmarkSample.risk_subtype_id == RiskSubtype.id,
                    BenchmarkSample.is_active.is_(True),
                ),
            )
            .where(
                RiskSubtype.is_active.is_(True),
                RiskSubtype.code.in_(ordered_dataset_ids),
            )
            .group_by(RiskSubtype.code, RiskSubtype.name)
        )
        dataset_rows = (await self.db.execute(dataset_stmt)).all()
        dataset_names = {code: name for code, name in dataset_rows}

        ordering = case(
            {dataset_id: index for index, dataset_id in enumerate(ordered_dataset_ids)},
            value=RiskSubtype.code,
        )
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
        if upper == 1.0:
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
            "matched_counts": {
                dataset_id: matched_counts.get(dataset_id, 0)
                for dataset_id in ordered_dataset_ids
            },
        }

    async def load_dataset_name_translations(
        self, locale: str, dataset_codes: list[str]
    ) -> dict[str, str]:
        """按公开数据集 ID 加载当前 locale 的展示名称翻译。"""
        if not locale or not dataset_codes:
            return {}
        rows = (
            await self.db.execute(
                select(RiskSubtype.code, RiskSubtype.translations).where(
                    RiskSubtype.code.in_(sorted(set(dataset_codes)))
                )
            )
        ).all()
        names: dict[str, str] = {}
        for code, translations in rows:
            if not isinstance(translations, dict):
                continue
            locale_translations = translations.get(locale)
            if not isinstance(locale_translations, dict):
                continue
            name = locale_translations.get("name")
            if isinstance(name, str) and name:
                names[str(code)] = name
        return names

    async def create_run_graph(
        self,
        run: TestRun,
        dataset_ids: list[str],
        dataset_names: dict[str, str],
        matched_counts: dict[str, int],
        sample_rows: list[BenchmarkSample],
    ) -> TestRun:
        """创建评测任务及关联执行图。"""
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

        current_difficulty_version = (
            await self.db.execute(
                select(DifficultyVersion)
                .where(DifficultyVersion.status == "published")
                .order_by(
                    DifficultyVersion.published_at.desc(), DifficultyVersion.id.desc()
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        difficulty_items: dict[int, DifficultyVersionItem] = {}
        if current_difficulty_version is not None and sample_rows:
            item_rows = list(
                (
                    await self.db.execute(
                        select(DifficultyVersionItem).where(
                            DifficultyVersionItem.version_id
                            == current_difficulty_version.id,
                            DifficultyVersionItem.sample_id_ref.in_(
                                [sample.id for sample in sample_rows]
                            ),
                        )
                    )
                ).scalars()
            )
            difficulty_items = {item.sample_id_ref: item for item in item_rows}

        run_samples: list[RunSample] = []
        for global_order, sample_row in enumerate(sample_rows, start=1):
            difficulty_item = difficulty_items.get(sample_row.id)
            difficulty_version_code = (
                current_difficulty_version.version_code
                if current_difficulty_version is not None
                and difficulty_item is not None
                else "legacy_current"
            )
            run_samples.append(
                RunSample(
                    run_id=run.id,
                    sample_id_ref=sample_row.id,
                    order_no=global_order,
                    difficulty_version_code=difficulty_version_code,
                    difficulty_score_snapshot=(
                        difficulty_item.difficulty_score
                        if difficulty_item is not None
                        else sample_row.difficulty_score
                    ),
                    completion_difficulty_snapshot=(
                        difficulty_item.completion_difficulty
                        if difficulty_item is not None
                        else sample_row.difficulty_score
                    ),
                    safety_difficulty_snapshot=(
                        difficulty_item.safety_difficulty
                        if difficulty_item is not None
                        else sample_row.difficulty_score
                    ),
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
                    status="blocked",
                    retry_no=0,
                    attempt_reason="initial",
                )
                for run_sample in run_samples
            ]
        )
        await self.db.flush()
        return run

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

    async def load_related_for_runs(
        self, run_ids: list[int]
    ) -> tuple[dict[int, list[RunDataset]], dict[int, RunReport]]:
        """批量加载列表页所需的数据集快照与报告摘要。"""
        if not run_ids:
            return {}, {}

        dataset_rows = list(
            (
                await self.db.execute(
                    select(RunDataset)
                    .where(RunDataset.run_id.in_(run_ids))
                    .order_by(
                        RunDataset.run_id.asc(),
                        RunDataset.order_no.asc(),
                        RunDataset.id.asc(),
                    )
                )
            ).scalars()
        )
        datasets_by_run: dict[int, list[RunDataset]] = defaultdict(list)
        for dataset in dataset_rows:
            datasets_by_run[dataset.run_id].append(dataset)

        report_rows = list(
            (
                await self.db.execute(
                    select(RunReport).where(RunReport.run_id.in_(run_ids))
                )
            ).scalars()
        )
        reports_by_run = {report.run_id: report for report in report_rows}
        return dict(datasets_by_run), reports_by_run

    async def load_scores_for_runs(
        self, run_ids: list[int]
    ) -> dict[int, EvaluationScore]:
        """批量加载评测任务评分。"""
        if not run_ids:
            return {}
        rows = list(
            (
                await self.db.execute(
                    select(EvaluationScore).where(EvaluationScore.run_id.in_(run_ids))
                )
            ).scalars()
        )
        return {row.run_id: row for row in rows}

    async def load_run_score(self, run_id: int) -> EvaluationScore | None:
        """加载单个评测任务评分。"""
        return (
            await self.db.execute(
                select(EvaluationScore).where(EvaluationScore.run_id == run_id)
            )
        ).scalar_one_or_none()

    async def load_report_execution_rows(self, run_id: int):
        """加载完整报告聚合所需的样本执行明细。"""
        latest_execution = aliased(SampleExecution)
        latest_retry_no = (
            select(latest_execution.retry_no)
            .where(latest_execution.run_sample_id == RunSample.id)
            .order_by(latest_execution.retry_no.desc(), latest_execution.id.desc())
            .limit(1)
            .correlate(RunSample)
            .scalar_subquery()
        )
        return (
            await self.db.execute(
                select(
                    RunSample.difficulty_score_snapshot,
                    RunSample.difficulty_version_code,
                    BenchmarkSample.sample_id,
                    RiskSubtype.code,
                    RiskSubtype.name,
                    SampleExecution.status,
                    SampleExecution.started_at,
                    SampleExecution.finished_at,
                    ExecutionSummary.task_completed,
                    ExecutionSummary.harm_detected,
                    ExecutionSummary.final_label,
                )
                .join(SampleExecution, SampleExecution.run_sample_id == RunSample.id)
                .join(BenchmarkSample, RunSample.sample_id_ref == BenchmarkSample.id)
                .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
                .outerjoin(
                    ExecutionSummary,
                    ExecutionSummary.sample_execution_id == SampleExecution.id,
                )
                .where(
                    RunSample.run_id == run_id,
                    SampleExecution.retry_no == latest_retry_no,
                )
                .order_by(RunSample.order_no.asc(), RunSample.id.asc())
            )
        ).all()

    async def commit(self) -> None:
        """提交评测任务相关事务。"""
        await self.db.commit()

    async def rollback(self) -> None:
        """回滚评测任务相关事务。"""
        await self.db.rollback()

    async def refresh(self, entity) -> None:
        """刷新指定实体的数据库状态。"""
        await self.db.refresh(entity)
