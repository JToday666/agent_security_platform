"""Persistence boundary for worker sample execution results."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete, select, update

from app.models.benchmark import SampleOracle
from app.models.benchmark_run import (
    ExecutionArtifact,
    ExecutionSummary,
    OracleResult,
    RunDataset,
    SampleExecution,
    TestRun,
)
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal
from app.worker.analysis.service import analyze_runtime_artifacts, summary_from_analysis
from app.worker.oracle_evaluator import (
    EVALUATOR_VERSION,
    evaluate_oracles_from_artifacts,
)
from app.worker.runtime import collect_artifacts


def now_utc() -> datetime:
    """Return current UTC time for worker audit columns."""
    return datetime.now(timezone.utc)


def to_error_message(exc: Exception) -> str:
    """Compress an exception into a persistable error summary."""
    text = f"{exc.__class__.__name__}: {exc}"
    return text[:2000]


def _claim_token_mismatch(
    execution: SampleExecution, claim_token: str | None
) -> bool:
    """Return True when a stale worker attempts to write with an old claim token."""
    return claim_token is not None and execution.claim_token != claim_token


async def mark_execution_dispatching(
    execution_id: int, *, claim_token: str | None = None
) -> bool:
    """Mark an execution as dispatching, returning False when it is terminal/missing."""
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if (
            execution is None
            or execution.status in {"done", "error", "canceled"}
            or _claim_token_mismatch(execution, claim_token)
        ):
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
    claim_token: str | None = None,
) -> None:
    """Persist sample execution summary, artifacts and aggregate counters."""
    finished_at = now_utc()

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if (
            execution is None
            or execution.status in {"done", "error", "canceled"}
            or _claim_token_mismatch(execution, claim_token)
        ):
            return

        await db.execute(
            delete(ExecutionArtifact).where(
                ExecutionArtifact.sample_execution_id == execution_id
            )
        )
        await db.execute(
            delete(ExecutionSummary).where(
                ExecutionSummary.sample_execution_id == execution_id
            )
        )
        await db.execute(
            delete(OracleResult).where(OracleResult.sample_execution_id == execution_id)
        )

        summary_payload = summary
        analysis_output_path = prepared.run_dir / "analysis_result.json"
        task_path = prepared.sample_dir / "task.json"
        if summary_payload is None:
            oracle_rows = (
                (
                    await db.execute(
                        select(SampleOracle).where(
                            SampleOracle.sample_id_ref == execution.sample_id_ref,
                            SampleOracle.is_active.is_(True),
                        )
                    )
                )
                .scalars()
                .all()
            )
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
        execution.claimed_by = None
        execution.claimed_at = None
        execution.claim_heartbeat_at = None
        execution.claim_token = None
        execution.lease_expires_at = None

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


async def persist_execution_artifacts_only(
    execution_id: int,
    *,
    prepared,
    claim_token: str | None = None,
) -> None:
    """Persist available artifacts for an execution that failed before summary."""
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if (
            execution is None
            or execution.status in {"done", "error", "canceled"}
            or _claim_token_mismatch(execution, claim_token)
        ):
            return

        await db.execute(
            delete(ExecutionArtifact).where(
                ExecutionArtifact.sample_execution_id == execution_id
            )
        )
        artifacts = await asyncio.to_thread(collect_artifacts, prepared)
        for artifact in artifacts:
            db.add(
                ExecutionArtifact(
                    sample_execution_id=execution_id,
                    artifact_type=artifact.artifact_type,
                    storage_uri=artifact.storage_uri,
                    artifact_metadata=artifact.metadata,
                )
            )
        await db.commit()


async def mark_execution_runtime_ready(
    execution_id: int, prepared, *, claim_token: str | None = None
) -> None:
    """Persist runtime workspace metadata after the probe backend is ready."""
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if (
            execution is None
            or execution.status in {"done", "error", "canceled"}
            or _claim_token_mismatch(execution, claim_token)
        ):
            return
        execution.work_dir = str(prepared.work_dir)
        execution.entry_url = prepared.public_entry_url or prepared.entry_url
        execution.environment_ref = prepared.environment_ref
        execution.status = "executing"
        execution.updated_at = now_utc()
        await db.commit()


async def mark_execution_state(
    execution_id: int, status: str, *, claim_token: str | None = None
) -> None:
    """Update one sample execution status."""
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if (
            execution is None
            or execution.status in {"done", "error", "canceled"}
            or _claim_token_mismatch(execution, claim_token)
        ):
            return
        execution.status = status
        execution.updated_at = now_utc()
        await db.commit()


async def mark_execution_system_error(
    execution_id: int,
    run_id: int,
    dataset_id: int,
    exc: Exception,
    *,
    claim_token: str | None = None,
) -> None:
    """Persist system-level execution errors and create a retry attempt when allowed."""
    finished_at = now_utc()
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if (
            execution is None
            or execution.status in {"done", "error", "canceled"}
            or _claim_token_mismatch(execution, claim_token)
        ):
            return
        next_retry_no = int(execution.retry_no) + 1
        execution.status = "error"
        execution.finished_at = finished_at
        execution.updated_at = finished_at
        execution.error_message = to_error_message(exc)
        execution.claimed_by = None
        execution.claimed_at = None
        execution.claim_heartbeat_at = None
        execution.claim_token = None
        execution.lease_expires_at = None

        if next_retry_no < max(1, settings.SAMPLE_MAX_ATTEMPTS):
            existing_retry = (
                await db.execute(
                    select(SampleExecution).where(
                        SampleExecution.run_sample_id == execution.run_sample_id,
                        SampleExecution.retry_no == next_retry_no,
                    )
                )
            ).scalar_one_or_none()
            if existing_retry is None:
                db.add(
                    SampleExecution(
                        run_id=execution.run_id,
                        run_sample_id=execution.run_sample_id,
                        sample_id_ref=execution.sample_id_ref,
                        status="ready",
                        retry_no=next_retry_no,
                        ready_at=finished_at,
                        attempt_reason="system_error_retry",
                    )
                )
            await db.commit()
            return

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
