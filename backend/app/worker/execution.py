"""Worker 数据集与样本执行逻辑。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update

from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import (
    ExecutionArtifact,
    ExecutionSummary,
    RunDataset,
    RunSample,
    SampleExecution,
    TestRun,
)
from app.shared.config import settings
from app.shared.db.session import AsyncSessionLocal
from app.worker.runtime import (
    RuntimeDispatchError,
    RuntimeDispatchTimeout,
    SampleRuntimeTarget,
    collect_artifacts,
    launch_runtime,
    prepare_runtime_workspace,
    resolve_dispatch_adapter,
    stop_runtime,
)
from app.worker.runtime.ports import allocate_tcp_port
from app.worker.runtime.preparation import build_environment_ref, build_probe_token


@dataclass(slots=True)
class SampleJob:
    """Immutable sample execution job snapshot."""

    execution_id: int
    sample: SampleRuntimeTarget


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_error_message(exc: Exception) -> str:
    text = f"{exc.__class__.__name__}: {exc}"
    return text[:2000]


def _execution_timeout_seconds(timeout_seconds: int | None) -> int:
    return max(1, int(timeout_seconds or settings.WORKER_EXECUTION_TIMEOUT_SECONDS))


def _summary_for_success(dispatch_mode: str) -> dict[str, object]:
    if dispatch_mode == "synthetic_local":
        return {
            "task_completed": False,
            "harm_detected": False,
            "summary_text": "已完成 runtime 启动、__probe__ 事件采集与 replay 证据生成；当前结果来自 synthetic_local 闭环，等待真实 Agent 接入后复核。",
            "final_label": "needs_review",
        }
    return {
        "task_completed": False,
        "harm_detected": False,
        "summary_text": "已完成 runtime 运行与证据采集，等待人工复核。",
        "final_label": "needs_review",
    }


def _summary_for_timeout() -> dict[str, object]:
    return {
        "task_completed": False,
        "harm_detected": False,
        "summary_text": "运行超时，未在限制时间内收到 finalize。",
        "final_label": "timeout",
    }


def _validate_dispatch_results(prepared, compile_result: dict[str, object], replay_result: dict[str, object]) -> None:
    if not (prepared.run_dir / "compile_result.json").exists():
        raise RuntimeDispatchError("compile_result.json not found")
    if not (prepared.run_dir / "replay_result.json").exists():
        raise RuntimeDispatchError("replay_result.json not found")

    if not compile_result:
        raise RuntimeDispatchError("compile result is empty")
    if compile_result.get("ok") is False:
        raise RuntimeDispatchError(str(compile_result.get("error") or "compiler returned ok=false"))
    if replay_result.get("ok") is False:
        raise RuntimeDispatchError(str(replay_result.get("error") or "replay returned ok=false"))
    if not replay_result:
        raise RuntimeDispatchError("replay result is empty")


async def _persist_runtime_result(
    execution_id: int,
    run_id: int,
    dataset_id: int,
    *,
    prepared,
    summary: dict[str, object],
    success: bool,
    final_status: str,
    error_message: str | None = None,
) -> None:
    artifacts = await asyncio.to_thread(collect_artifacts, prepared)
    finished_at = _now()

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None:
            return

        await db.execute(delete(ExecutionArtifact).where(ExecutionArtifact.sample_execution_id == execution_id))
        await db.execute(delete(ExecutionSummary).where(ExecutionSummary.sample_execution_id == execution_id))

        db.add(
            ExecutionSummary(
                sample_execution_id=execution_id,
                task_completed=bool(summary["task_completed"]),
                harm_detected=bool(summary["harm_detected"]),
                summary_text=str(summary["summary_text"]),
                final_label=str(summary["final_label"]),
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


async def _mark_execution_runtime_ready(execution_id: int, prepared) -> None:
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None:
            return
        execution.work_dir = str(prepared.work_dir)
        execution.entry_url = prepared.entry_url
        execution.environment_ref = prepared.environment_ref
        execution.status = "executing"
        execution.updated_at = _now()
        await db.commit()


async def _mark_execution_state(execution_id: int, status: str) -> None:
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None:
            return
        execution.status = status
        execution.updated_at = _now()
        await db.commit()


async def _mark_execution_system_error(execution_id: int, run_id: int, dataset_id: int, exc: Exception) -> None:
    finished_at = _now()
    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None:
            return
        execution.status = "error"
        execution.finished_at = finished_at
        execution.updated_at = finished_at
        execution.error_message = _to_error_message(exc)
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


def _resolve_dispatch_mode(explicit_mode: str | None) -> str:
    normalized = (explicit_mode or settings.WORKER_DISPATCH_MODE_DEFAULT or "synthetic_local").strip().lower()
    return normalized or "synthetic_local"


async def execute_sample(
    run_id: int,
    dataset_id: int,
    job: SampleJob,
    *,
    dispatch_mode: str | None = None,
    timeout_seconds: int | None = None,
) -> None:
    """Execute a single sample against the shared __probe__ runtime."""
    execution_id = job.execution_id
    sample = job.sample
    timeout = _execution_timeout_seconds(timeout_seconds)
    resolved_dispatch_mode = _resolve_dispatch_mode(dispatch_mode)

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, execution_id)
        if execution is None or execution.status in {"done", "error"}:
            return
        execution.status = "dispatching"
        execution.started_at = execution.started_at or _now()
        execution.updated_at = _now()
        execution.error_message = None
        await db.commit()

    environment_ref = build_environment_ref(execution_id)
    probe_token = build_probe_token()
    port = allocate_tcp_port(settings.WORKER_RUNNER_HOST)
    prepared = await asyncio.to_thread(
        prepare_runtime_workspace,
        sample,
        execution_id,
        settings.worker_workdir_root,
        settings.WORKER_RUNNER_HOST,
        port,
        environment_ref,
        probe_token,
    )
    handle = None

    try:
        handle = await launch_runtime(prepared)
        await _mark_execution_runtime_ready(execution_id, prepared)

        adapter = resolve_dispatch_adapter(resolved_dispatch_mode)
        dispatch_result = await adapter.dispatch(prepared, sample, timeout)

        await _mark_execution_state(execution_id, "verifying")
        _validate_dispatch_results(prepared, dispatch_result.compile_result, dispatch_result.replay_result)

        await _persist_runtime_result(
            execution_id,
            run_id,
            dataset_id,
            prepared=prepared,
            summary=_summary_for_success(dispatch_result.mode),
            success=True,
            final_status="done",
        )
    except RuntimeDispatchTimeout:
        await _persist_runtime_result(
            execution_id,
            run_id,
            dataset_id,
            prepared=prepared,
            summary=_summary_for_timeout(),
            success=True,
            final_status="done",
        )
    except Exception as exc:
        await _mark_execution_system_error(execution_id, run_id, dataset_id, exc)
    finally:
        if handle is not None:
            await stop_runtime(handle)


async def _load_sample_jobs(run_id: int, dataset_code: str) -> list[SampleJob]:
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
                .join(BenchmarkSample, SampleExecution.sample_id_ref == BenchmarkSample.id)
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
    for execution_id, status, sample_db_id, sample_id, sample_name, resource_path, entry_path, user_goal in rows:
        if status in {"done", "error"}:
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


async def _mark_dataset_completed(run_id: int, dataset_id: int, dataset_code: str) -> None:
    finished_at = _now()
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


async def execute_dataset(
    run_id: int,
    dataset_id: int,
    dataset_code: str,
    *,
    dispatch_mode: str | None = None,
    timeout_seconds: int | None = None,
) -> None:
    """Execute every sample in one dataset with bounded parallelism."""
    jobs = await _load_sample_jobs(run_id, dataset_code)
    semaphore = asyncio.Semaphore(max(1, settings.WORKER_MAX_PARALLEL_EXECUTIONS_PER_RUN))

    async def run_job(job: SampleJob) -> None:
        async with semaphore:
            await execute_sample(
                run_id,
                dataset_id,
                job,
                dispatch_mode=dispatch_mode,
                timeout_seconds=timeout_seconds,
            )

    await asyncio.gather(*(run_job(job) for job in jobs))
    await _mark_dataset_completed(run_id, dataset_id, dataset_code)
