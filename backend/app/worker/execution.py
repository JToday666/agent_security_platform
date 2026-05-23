"""Worker dataset and sample execution orchestration."""

from __future__ import annotations

import asyncio

from app.platform.config import settings
from app.worker.execution_concurrency import (
    runtime_process_semaphore as _runtime_process_semaphore,
)
from app.worker.execution_jobs import SampleJob, load_sample_jobs
from app.worker.execution_persistence import (
    mark_dataset_completed,
    mark_execution_dispatching,
    mark_execution_runtime_ready,
    mark_execution_state,
    mark_execution_system_error,
    persist_runtime_result,
)
from app.worker.runtime import (
    RuntimeDispatchError,
    RuntimeDispatchTimeout,
    launch_runtime,
    prepare_runtime_workspace,
    resolve_dispatch_adapter,
    stop_runtime,
)
from app.worker.runtime.ports import allocate_tcp_port
from app.worker.runtime.preparation import build_environment_ref, build_probe_token


def _execution_timeout_seconds(timeout_seconds: int | None) -> int:
    """Resolve per-sample execution timeout."""
    return max(1, int(timeout_seconds or settings.WORKER_EXECUTION_TIMEOUT_SECONDS))


def _summary_for_timeout() -> dict[str, object]:
    """Build the summary persisted when dispatch times out."""
    return {
        "task_completed": False,
        "harm_detected": False,
        "summary_text": "运行超时，未在限制时间内收到 finalize。",
        "final_label": "timeout",
    }


def _validate_dispatch_results(prepared, finalized: bool) -> None:
    """Ensure runtime dispatch finalized and produced its minimum evidence."""
    if not finalized:
        raise RuntimeDispatchError("runtime dispatch did not finalize")
    if not (prepared.run_dir / "finalize.json").exists():
        raise RuntimeDispatchError("finalize.json not found")


def _resolve_dispatch_mode(explicit_mode: str | None) -> str:
    """Resolve the runtime dispatch mode for the current sample."""
    normalized = (
        (explicit_mode or settings.WORKER_DISPATCH_MODE_DEFAULT or "synthetic_local")
        .strip()
        .lower()
    )
    return normalized or "synthetic_local"


def _resolve_browser_entry_host() -> str:
    """Resolve the host embedded in URLs sent to browser-driving agents."""
    browser_host = (settings.WORKER_BROWSER_ENTRY_HOST or "").strip()
    return browser_host or settings.WORKER_RUNNER_HOST


async def execute_sample(
    run_id: int,
    dataset_id: int,
    job: SampleJob,
    *,
    dispatch_mode: str | None = None,
    dispatch_config: dict[str, object] | None = None,
    timeout_seconds: int | None = None,
) -> None:
    """Execute one sample through runtime launch, dispatch, verification and persistence."""
    execution_id = job.execution_id
    sample = job.sample
    timeout = _execution_timeout_seconds(timeout_seconds)
    resolved_dispatch_mode = _resolve_dispatch_mode(dispatch_mode)

    should_execute = await mark_execution_dispatching(execution_id)
    if not should_execute:
        return

    environment_ref = build_environment_ref(execution_id)
    probe_token = build_probe_token()
    port = allocate_tcp_port(settings.WORKER_RUNNER_HOST)
    prepared = await asyncio.to_thread(
        prepare_runtime_workspace,
        sample,
        execution_id,
        settings.worker_workdir_root,
        _resolve_browser_entry_host(),
        port,
        environment_ref,
        probe_token,
    )
    handle = None

    async with _runtime_process_semaphore():
        try:
            handle = await launch_runtime(prepared)
            await mark_execution_runtime_ready(execution_id, prepared)

            adapter = resolve_dispatch_adapter(resolved_dispatch_mode)
            dispatch_result = await adapter.dispatch(
                prepared, sample, timeout, dispatch_config=dispatch_config
            )

            await mark_execution_state(execution_id, "verifying")
            _validate_dispatch_results(prepared, dispatch_result.finalized)

            await persist_runtime_result(
                execution_id,
                run_id,
                dataset_id,
                prepared=prepared,
                summary=None,
                success=True,
                final_status="done",
            )
        except RuntimeDispatchTimeout:
            await persist_runtime_result(
                execution_id,
                run_id,
                dataset_id,
                prepared=prepared,
                summary=_summary_for_timeout(),
                success=True,
                final_status="done",
            )
        except Exception as exc:
            await mark_execution_system_error(execution_id, run_id, dataset_id, exc)
        finally:
            if handle is not None:
                await stop_runtime(handle)


async def execute_dataset(
    run_id: int,
    dataset_id: int,
    dataset_code: str,
    *,
    dispatch_mode: str | None = None,
    dispatch_config: dict[str, object] | None = None,
    timeout_seconds: int | None = None,
) -> None:
    """Execute all pending samples for one dataset under configured concurrency."""
    jobs = await load_sample_jobs(run_id, dataset_code)
    semaphore = asyncio.Semaphore(
        max(1, settings.WORKER_MAX_PARALLEL_EXECUTIONS_PER_RUN)
    )

    async def run_job(job: SampleJob) -> None:
        async with semaphore:
            await execute_sample(
                run_id,
                dataset_id,
                job,
                dispatch_mode=dispatch_mode,
                dispatch_config=dispatch_config,
                timeout_seconds=timeout_seconds,
            )

    await asyncio.gather(*(run_job(job) for job in jobs))
    await mark_dataset_completed(run_id, dataset_id, dataset_code)
