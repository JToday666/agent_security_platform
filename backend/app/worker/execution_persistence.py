"""Persistence boundary for worker sample execution results."""

from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

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
from app.platform.observability import (
    SampleExecutionEventType,
    record_sample_execution_event,
)
from app.worker.analysis.service import analyze_runtime_artifacts, summary_from_analysis
from app.worker.oracle_evaluator import (
    EVALUATOR_VERSION,
    evaluate_oracles_from_artifacts,
)
from app.worker.runtime import ArtifactRecord, collect_artifacts


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


def _system_error_retries_enabled(run: TestRun | None) -> bool:
    """Return whether system-error retries are enabled for a run."""
    if run is None or not isinstance(run.execution_config, dict):
        return True
    parameters = run.execution_config.get("parameters")
    if not isinstance(parameters, dict):
        return True
    return parameters.get("retryEnabled") is not False


def _archive_relative_path(prepared, artifact: ArtifactRecord) -> Path:
    try:
        return artifact.path.relative_to(prepared.run_dir)
    except ValueError:
        return Path(str(artifact.metadata.get("relativePath") or artifact.path.name))


def _archive_artifacts(
    *, run_id: int, execution_id: int, prepared, artifacts: list[ArtifactRecord]
) -> list[ArtifactRecord]:
    """Copy runtime workdir artifacts into the durable artifact root."""
    archived: list[ArtifactRecord] = []
    sample_root = (
        settings.artifact_root
        / "evaluations"
        / str(run_id)
        / "samples"
        / str(execution_id)
    )
    for artifact in artifacts:
        relative_path = _archive_relative_path(prepared, artifact)
        target_path = sample_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact.path, target_path)
        stat = target_path.stat()
        artifact_relative_path = relative_path.as_posix()
        source_relative_path = str(
            artifact.metadata.get("relativePath") or artifact_relative_path
        )
        archived.append(
            ArtifactRecord(
                artifact_type=artifact.artifact_type,
                path=target_path,
                storage_uri=(
                    f"artifact://evaluations/{run_id}/samples/"
                    f"{execution_id}/{artifact_relative_path}"
                ),
                metadata={
                    **artifact.metadata,
                    "sourceRelativePath": source_relative_path,
                    "artifactRelativePath": artifact_relative_path,
                    "sizeBytes": stat.st_size,
                },
            )
        )
    manifest_path = sample_root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_payload = {
        "schemaVersion": 1,
        "runId": run_id,
        "sampleExecutionId": execution_id,
        "sampleArtifactUri": f"artifact://evaluations/{run_id}/samples/{execution_id}/",
        "generatedAt": now_utc().isoformat(),
        "artifactCount": len(archived),
        "artifacts": [
            {
                "type": artifact.artifact_type,
                "uri": artifact.storage_uri,
                "relativePath": artifact.metadata.get("artifactRelativePath"),
                "sourceRelativePath": artifact.metadata.get("sourceRelativePath"),
                "sizeBytes": artifact.metadata.get("sizeBytes"),
            }
            for artifact in archived
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest_stat = manifest_path.stat()
    archived.append(
        ArtifactRecord(
            artifact_type="artifact_manifest",
            path=manifest_path,
            storage_uri=(
                f"artifact://evaluations/{run_id}/samples/{execution_id}/manifest.json"
            ),
            metadata={
                "artifactRelativePath": "manifest.json",
                "sourceRelativePath": "manifest.json",
                "sizeBytes": manifest_stat.st_size,
                "manifestVersion": 1,
                "listedArtifactCount": manifest_payload["artifactCount"],
            },
        )
    )
    return archived


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
        artifacts = await asyncio.to_thread(
            _archive_artifacts,
            run_id=run_id,
            execution_id=execution_id,
            prepared=prepared,
            artifacts=artifacts,
        )

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
        await record_sample_execution_event(
            db,
            run_id=run_id,
            sample_execution_id=execution_id,
            event_type=SampleExecutionEventType.ARTIFACT_PERSISTED,
            status="persisted",
            message="Execution artifacts persisted",
            payload={
                "artifactCount": len(artifacts),
                "artifactTypes": sorted({artifact.artifact_type for artifact in artifacts}),
            },
        )
        await record_sample_execution_event(
            db,
            run_id=run_id,
            sample_execution_id=execution_id,
            event_type=SampleExecutionEventType.ORACLE_JUDGEMENT_FINISHED,
            status=str(summary_payload["final_label"]),
            message="Oracle judgement finished",
            payload={
                "taskCompleted": bool(summary_payload["task_completed"]),
                "harmDetected": bool(summary_payload["harm_detected"]),
                "finalLabel": str(summary_payload["final_label"]),
            },
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
        artifacts = await asyncio.to_thread(
            _archive_artifacts,
            run_id=execution.run_id,
            execution_id=execution_id,
            prepared=prepared,
            artifacts=artifacts,
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
        await record_sample_execution_event(
            db,
            run_id=execution.run_id,
            sample_execution_id=execution_id,
            event_type=SampleExecutionEventType.ARTIFACT_PERSISTED,
            status="persisted",
            message="Available execution artifacts persisted",
            payload={
                "artifactCount": len(artifacts),
                "artifactTypes": sorted({artifact.artifact_type for artifact in artifacts}),
            },
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

        run = await db.get(TestRun, run_id)
        retry_allowed = (
            next_retry_no < max(1, settings.SAMPLE_MAX_ATTEMPTS)
            and _system_error_retries_enabled(run)
        )
        if retry_allowed:
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
