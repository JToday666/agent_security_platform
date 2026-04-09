"""Worker 数据集与样本执行逻辑。"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.models.benchmark import BenchmarkSample, RiskSubtype, SampleOracle
from app.models.benchmark_run import ExecutionSummary, OracleResult, RunDataset, RunSample, SampleExecution


def deterministic_sample_outcome(run_id: int, sample_id: int) -> tuple[bool, bool]:
    """生成样本执行的模拟结果。"""
    digest = hashlib.sha1(f"{run_id}:{sample_id}".encode("utf-8")).hexdigest()
    seed = int(digest[:8], 16)
    harm_detected = seed % 5 == 0
    task_completed = seed % 7 != 0
    return harm_detected, task_completed


def build_final_label(task_completed: bool, harm_detected: bool) -> str:
    """根据执行结果生成最终标签。"""
    if harm_detected:
        return "hijacked"
    if task_completed:
        return "safe"
    return "refused"


async def execute_sample(db, run, execution: SampleExecution, sample: BenchmarkSample) -> None:
    """执行单个样本并写入判定结果。"""
    now = datetime.now(timezone.utc)
    execution.status = "executing"
    execution.started_at = execution.started_at or now
    await db.flush()

    harm_detected, task_completed = deterministic_sample_outcome(run.id, sample.id)
    execution.status = "done"
    finished_at = datetime.now(timezone.utc)
    execution.finished_at = finished_at
    execution.updated_at = finished_at

    db.add(
        ExecutionSummary(
            sample_execution_id=execution.id,
            task_completed=task_completed,
            harm_detected=harm_detected,
            summary_text="模拟联调执行结果",
            final_label=build_final_label(task_completed=task_completed, harm_detected=harm_detected),
        )
    )

    oracles = list(
        (
            await db.execute(
                select(SampleOracle).where(
                    SampleOracle.sample_id_ref == sample.id,
                    SampleOracle.is_active.is_(True),
                )
            )
        ).scalars()
    )
    for oracle in oracles:
        matched = task_completed and not harm_detected if oracle.oracle_kind == 1 else harm_detected
        db.add(
            OracleResult(
                sample_execution_id=execution.id,
                oracle_id=oracle.id,
                matched=matched,
                score=Decimal("1.000") if matched else Decimal("0.000"),
                evidence_summary="模拟联调证据摘要",
                evidence_ref={"source": "worker", "oracleKind": oracle.oracle_kind},
                evaluator_version="worker-v1",
            )
        )

    run.completed_samples += 1
    run.success_count += 1
    await db.flush()


async def execute_dataset(db, run, dataset: RunDataset) -> None:
    """推进指定数据集下所有样本的执行状态。"""
    rows = (
        await db.execute(
            select(RunSample, BenchmarkSample)
            .join(BenchmarkSample, RunSample.sample_id_ref == BenchmarkSample.id)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(RunSample.run_id == run.id, RiskSubtype.code == dataset.dataset_code)
            .order_by(RunSample.order_no.asc(), RunSample.id.asc())
        )
    ).all()

    completed = 0
    for run_sample, sample in rows:
        execution = (
            await db.execute(
                select(SampleExecution).where(
                    SampleExecution.run_sample_id == run_sample.id,
                    SampleExecution.retry_no == 0,
                )
            )
        ).scalar_one()

        if execution.status == "done":
            completed += 1
            continue

        await execute_sample(db, run, execution, sample)
        completed += 1

    dataset.completed_samples = completed
    dataset.status = "completed"
    finished_time = datetime.now(timezone.utc)
    dataset.finished_at = finished_time
    dataset.updated_at = finished_time
    await db.commit()
