"""Persistence boundary for worker sample execution results."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update

from app.models.benchmark import BenchmarkSample, RiskSubtype, SampleOracle
from app.models.benchmark_run import (
    ExecutionArtifact,
    ExecutionSummary,
    OracleResult,
    RunDataset,
    RunSample,
    SampleExecution,
    TestRun,
)
from app.platform.db.session import AsyncSessionLocal
from app.worker.analysis.service import analyze_runtime_artifacts, summary_from_analysis
from app.worker.oracle_evaluator import EVALUATOR_VERSION, evaluate_oracles_from_artifacts
from app.worker.runtime import collect_artifacts


def now_utc() -> datetime:
    """Return current UTC time for worker audit columns."""
    return datetime.now(timezone.utc)


def to_error_message(exc: Exception) -> str:
    """Compress an exception into a persistable error summary."""
    text = f"{exc.__class__.__name__}: {exc}"
    return text[:2000]


async def mark_execution_dispatching(execution_id: int) -> bool:
    """Mark an execution as dispatching, returning False when it is terminal/missing."""
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None or execution.status in {"done", "error"}:
            return False
        current_time = now_utc()
        execution.status = "dispatching"
        execution.started_at = execution.started_at or current_time
        execution.updated_at = current_time
        execution.error_message = None
        await db.commit()
        return True


async def persist_runtime_result(
    execution_id: int,
    run_id: int,
    dataset_id: int,
    *,
    prepared,
    summary: dict[str, object] | None,
    success: bool,
    final_status: str,
    error_message: str | None = None,
) -> None:
    """Persist sample execution summary, artifacts and aggregate counters."""
    finished_at = now_utc()

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None:
            return

        await db.execute(delete(ExecutionArtifact).where(ExecutionArtifact.sample_execution_id == execution_id))
        await db.execute(delete(ExecutionSummary).where(ExecutionSummary.sample_execution_id == execution_id))
        await db.execute(delete(OracleResult).where(OracleResult.sample_execution_id == execution_id))

        summary_payload = summary
        analysis_output_path = prepared.run_dir / "analysis_result.json"
        task_path = prepared.sample_dir / "task.json"
        if summary_payload is None:
            oracle_rows = (
                await db.execute(
                    select(SampleOracle).where(
                        SampleOracle.sample_id_ref == execution.sample_id_ref,
                        SampleOracle.is_active.is_(True),
                    )
                )
            ).scalars().all()
            if oracle_rows:
                evaluation_bundle = await asyncio.to_thread(
                    evaluate_oracles_from_artifacts,
                    oracle_rows,
                    prepared.run_dir,
                    task_path=task_path if task_path.exists() else None,
                    output_path=analysis_output_path,
                )
                for result in evaluation_bundle.results:
                    db.add(
                        OracleResult(
                            sample_execution_id=execution_id,
                            oracle_id=result.oracle_id,
                            matched=result.matched,
                            score=result.score,
                            evidence_summary=result.evidence_summary,
                            evidence_ref=result.evidence_ref,
                            evaluator_version=EVALUATOR_VERSION,
                        )
                    )
                summary_payload = evaluation_bundle.summary
            else:
                analysis_result = await asyncio.to_thread(
                    analyze_runtime_artifacts,
                    run_dir=prepared.run_dir,
                    task_path=task_path if task_path.exists() else None,
                    output_path=analysis_output_path,
                )
                summary_payload = summary_from_analysis(analysis_result)
        elif task_path.exists():
            await asyncio.to_thread(
                analyze_runtime_artifacts,
                run_dir=prepared.run_dir,
                task_path=task_path,
                output_path=analysis_output_path,
            )

        artifacts = await asyncio.to_thread(collect_artifacts, prepared)

        db.add(
            ExecutionSummary(
                sample_execution_id=execution_id,
                task_completed=bool(summary_payload["task_completed"]),
                harm_detected=bool(summary_payload["harm_detected"]),
                summary_text=str(summary_payload["summary_text"]),
                final_label=str(summary_payload["final_label"]),
            )
        )

        for artifact in artifacts:
            db.add(
                ExecutionArtifact(
                    sample_execution_id=execution_id,
                    artifact_type=artifact.artifact_type,
                    storage_uri=artifact.storage_uri,
                    artifact_metadata=artifact.metadata,
                )
            )

        execution.status = final_status
        execution.finished_at = finished_at
        execution.updated_at = finished_at
        execution.error_message = error_message

        await db.execute(
            update(TestRun)
            .where(TestRun.id == run_id)
            .values(
                completed_samples=TestRun.completed_samples + 1,
                success_count=TestRun.success_count + (1 if success else 0),
                failed_count=TestRun.failed_count + (0 if success else 1),
                updated_at=finished_at,
            )
        )
        await db.execute(
            update(RunDataset)
            .where(RunDataset.id == dataset_id)
            .values(
                completed_samples=RunDataset.completed_samples + 1,
                updated_at=finished_at,
            )
        )
        await db.commit()


async def mark_execution_runtime_ready(execution_id: int, prepared) -> None:
    """Persist runtime workspace metadata after the probe backend is ready."""
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None:
            return
        execution.work_dir = str(prepared.work_dir)
        execution.entry_url = prepared.entry_url
        execution.environment_ref = prepared.environment_ref
        execution.status = "executing"
        execution.updated_at = now_utc()
        await db.commit()


async def mark_execution_state(execution_id: int, status: str) -> None:
    """Update one sample execution status."""
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None:
            return
        execution.status = status
        execution.updated_at = now_utc()
        await db.commit()


async def mark_execution_system_error(execution_id: int, run_id: int, dataset_id: int, exc: Exception) -> None:
    """Persist system-level execution errors and failed counters."""
    finished_at = now_utc()
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None:
            return
        execution.status = "error"
        execution.finished_at = finished_at
        execution.updated_at = finished_at
        execution.error_message = to_error_message(exc)
        await db.execute(
            update(TestRun)
            .where(TestRun.id == run_id)
            .values(
                completed_samples=TestRun.completed_samples + 1,
                failed_count=TestRun.failed_count + 1,
                updated_at=finished_at,
            )
        )
        await db.execute(
            update(RunDataset)
            .where(RunDataset.id == dataset_id)
            .values(
                completed_samples=RunDataset.completed_samples + 1,
                updated_at=finished_at,
            )
        )
        await db.commit()


async def mark_dataset_completed(run_id: int, dataset_id: int, dataset_code: str) -> None:
    """Persist dataset-level completion after all sample jobs are terminal."""
    finished_at = now_utc()
    async with AsyncSessionLocal() as db:
        terminal_count = (
            await db.execute(
                select(func.count())
                .select_from(SampleExecution)
                .join(RunSample, SampleExecution.run_sample_id == RunSample.id)
                .join(BenchmarkSample, SampleExecution.sample_id_ref == BenchmarkSample.id)
                .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
                .where(
                    SampleExecution.run_id == run_id,
                    SampleExecution.retry_no == 0,
                    SampleExecution.status.in_(["done", "error"]),
                    RiskSubtype.code == dataset_code,
                )
            )
        ).scalar_one()

        dataset = await db.get(RunDataset, dataset_id)
        if dataset is None:
            return
        dataset.completed_samples = int(terminal_count or 0)
        dataset.status = "completed"
        dataset.finished_at = finished_at
        dataset.updated_at = finished_at
        await db.commit()

