"""Worker dataset and sample execution orchestration."""

from __future__ import annotations

import asyncio
import contextlib
import logging

from app.platform.config import settings
from app.modules.runtime_gateway.session_store import (
    close_runtime_session,
    create_runtime_session,
)
from app.worker.execution_concurrency import (
    runtime_process_semaphore as _runtime_process_semaphore,
)
from app.worker.execution_jobs import SampleJob
from app.worker.execution_persistence import (
    mark_execution_dispatching,
    mark_execution_runtime_ready,
    mark_execution_state,
    mark_execution_system_error,
    persist_execution_artifacts_only,
    persist_runtime_result,
)
from app.worker.runtime import (
    RuntimeDispatchCanceled,
    RuntimeDispatchError,
    RuntimeDispatchTimeout,
    launch_runtime,
    prepare_runtime_workspace,
    resolve_dispatch_adapter,
    stop_runtime,
)
from app.worker.runtime.ports import allocate_tcp_port
from app.worker.runtime.preparation import build_environment_ref, build_probe_token

LOGGER = logging.getLogger(__name__)


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


def _summary_for_cancel() -> dict[str, object]:
    """Build the summary persisted when a sample execution is canceled."""
    return {
        "task_completed": False,
        "harm_detected": False,
        "summary_text": "运行已取消。",
        "final_label": "canceled",
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
    claim_token: str | None = None,
) -> None:
    """Execute one sample through runtime launch, dispatch, verification and persistence."""
    execution_id = job.execution_id
    sample = job.sample
    timeout = _execution_timeout_seconds(timeout_seconds)
    resolved_dispatch_mode = _resolve_dispatch_mode(dispatch_mode)

    should_execute = await mark_execution_dispatching(
        execution_id, claim_token=claim_token
    )
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
        run_id,
    )
    handle = None

    async with _runtime_process_semaphore():
        try:
            handle = await launch_runtime(prepared)
            await create_runtime_session(
                prepared=prepared, run_id=run_id, timeout_seconds=timeout
            )
            await mark_execution_runtime_ready(
                execution_id, prepared, claim_token=claim_token
            )

            adapter = resolve_dispatch_adapter(resolved_dispatch_mode)
            effective_dispatch_config = dict(dispatch_config or {})
            effective_dispatch_config["runId"] = run_id
            dispatch_result = await adapter.dispatch(
                prepared, sample, timeout, dispatch_config=effective_dispatch_config
            )

            await mark_execution_state(
                execution_id, "verifying", claim_token=claim_token
            )
            _validate_dispatch_results(prepared, dispatch_result.finalized)

            await persist_runtime_result(
                execution_id,
                run_id,
                dataset_id,
                prepared=prepared,
                summary=None,
                success=True,
                final_status="done",
                claim_token=claim_token,
            )
            with contextlib.suppress(Exception):
                await close_runtime_session(execution_id, status="closed")
        except RuntimeDispatchTimeout:
            await persist_runtime_result(
                execution_id,
                run_id,
                dataset_id,
                prepared=prepared,
                summary=_summary_for_timeout(),
                success=True,
                final_status="done",
                claim_token=claim_token,
            )
            with contextlib.suppress(Exception):
                await close_runtime_session(execution_id, status="expired")
        except RuntimeDispatchCanceled as exc:
            await persist_runtime_result(
                execution_id,
                run_id,
                dataset_id,
                prepared=prepared,
                summary=_summary_for_cancel(),
                success=False,
                final_status="canceled",
                error_message=str(exc),
                claim_token=claim_token,
            )
            with contextlib.suppress(Exception):
                await close_runtime_session(execution_id, status="closed")
        except Exception as exc:
            with contextlib.suppress(Exception):
                await close_runtime_session(execution_id, status="error")
            with contextlib.suppress(Exception):
                await persist_execution_artifacts_only(
                    execution_id, prepared=prepared, claim_token=claim_token
                )
            LOGGER.exception(
                "sample_execution_dispatch_failed",
                extra={
                    "sample_execution_id": execution_id,
                    "run_id": run_id,
                    "dataset_id": dataset_id,
                    "dispatch_mode": resolved_dispatch_mode,
                },
            )
            await mark_execution_system_error(
                execution_id, run_id, dataset_id, exc, claim_token=claim_token
            )
        finally:
            if handle is not None:
                await stop_runtime(handle)
