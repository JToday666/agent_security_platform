"""Sample job loading for worker execution."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import RunSample, SampleExecution
from app.platform.db.session import AsyncSessionLocal
from app.worker.runtime import SampleRuntimeTarget


@dataclass(slots=True)
class SampleJob:
    """Lightweight snapshot for one sample execution."""

    execution_id: int
    sample: SampleRuntimeTarget


@dataclass(slots=True)
class SampleExecutionJob:
    """Executable sample job plus run and dataset context."""

    run_id: int
    dataset_id: int
    run_public_id: str
    execution_config: dict[str, object]
    job: SampleJob


async def load_sample_jobs(run_id: int, dataset_code: str) -> list[SampleJob]:
    """Load non-terminal sample execution jobs for one run dataset."""
    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(
                    SampleExecution.id,
                    SampleExecution.status,
                    BenchmarkSample.id,
                    BenchmarkSample.sample_id,
                    BenchmarkSample.sample_name,
                    BenchmarkSample.resource_path,
                    BenchmarkSample.entry_path,
                    BenchmarkSample.user_goal,
                )
                .join(RunSample, SampleExecution.run_sample_id == RunSample.id)
                .join(
                    BenchmarkSample, SampleExecution.sample_id_ref == BenchmarkSample.id
                )
                .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
                .where(
                    SampleExecution.run_id == run_id,
                    SampleExecution.retry_no == 0,
                    RiskSubtype.code == dataset_code,
                )
                .order_by(RunSample.order_no.asc(), RunSample.id.asc())
            )
        ).all()

    jobs: list[SampleJob] = []
    for (
        execution_id,
        status,
        sample_db_id,
        sample_id,
        sample_name,
        resource_path,
        entry_path,
        user_goal,
    ) in rows:
        if status in {"done", "error", "canceled"}:
            continue
        jobs.append(
            SampleJob(
                execution_id=execution_id,
                sample=SampleRuntimeTarget(
                    sample_db_id=sample_db_id,
                    sample_id=sample_id,
                    sample_name=sample_name or sample_id,
                    resource_path=resource_path,
                    entry_path=entry_path,
                    user_goal=user_goal,
                ),
            )
        )
    return jobs


async def load_sample_job_by_execution_id(
    execution_id: int,
) -> SampleExecutionJob | None:
    """Load the complete execution context for one claimed sample execution."""
    from app.models.benchmark_run import RunDataset, TestRun

    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(
                    SampleExecution.id,
                    TestRun.id,
                    TestRun.public_id,
                    TestRun.execution_config,
                    RunDataset.id,
                    BenchmarkSample.id,
                    BenchmarkSample.sample_id,
                    BenchmarkSample.sample_name,
                    BenchmarkSample.resource_path,
                    BenchmarkSample.entry_path,
                    BenchmarkSample.user_goal,
                )
                .join(TestRun, SampleExecution.run_id == TestRun.id)
                .join(RunSample, SampleExecution.run_sample_id == RunSample.id)
                .join(
                    BenchmarkSample, SampleExecution.sample_id_ref == BenchmarkSample.id
                )
                .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
                .join(
                    RunDataset,
                    (RunDataset.run_id == SampleExecution.run_id)
                    & (RunDataset.dataset_code == RiskSubtype.code),
                )
                .where(SampleExecution.id == execution_id)
            )
        ).one_or_none()

    if row is None:
        return None

    (
        loaded_execution_id,
        run_id,
        run_public_id,
        execution_config,
        dataset_id,
        sample_db_id,
        sample_id,
        sample_name,
        resource_path,
        entry_path,
        user_goal,
    ) = row
    return SampleExecutionJob(
        run_id=run_id,
        dataset_id=dataset_id,
        run_public_id=run_public_id,
        execution_config=(
            execution_config if isinstance(execution_config, dict) else {}
        ),
        job=SampleJob(
            execution_id=loaded_execution_id,
            sample=SampleRuntimeTarget(
                sample_db_id=sample_db_id,
                sample_id=sample_id,
                sample_name=sample_name or sample_id,
                resource_path=resource_path,
                entry_path=entry_path,
                user_goal=user_goal,
            ),
        ),
    )
