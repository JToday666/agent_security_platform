from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import ExecutionArtifact, ExecutionSummary, RunDataset, RunReport, SampleExecution, TestRun
from app.shared.config import settings
from app.shared.runtime_rules import difficulty_bucket_bounds


DATASET_ID = "B2_cloud_file_modification"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
CORE_ARTIFACT_TYPES = {"event_log", "compile_result", "replay_result"}
RUN_TERMINAL_STATUSES = {"completed", "terminated", "canceled", "failed"}
SUCCESS_LABELS = {"needs_review", "timeout"}

SYNC_ENGINE = create_engine(settings.SYNC_DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=SYNC_ENGINE, future=True)


@dataclass(slots=True)
class SpawnedService:
    name: str
    process: subprocess.Popen[str]
    log_path: Path


@dataclass(slots=True)
class RunSnapshot:
    evaluation_id: str
    run_id: int
    run_status: str
    finalization_reason: str | None
    dataset_statuses: dict[str, str]
    sample_statuses: list[str]
    sample_errors: list[str]
    artifact_types: set[str]
    final_labels: set[str]
    report_summary: dict[str, Any] | None
    runtime_paths: list[str]


class E2ELocalRunError(RuntimeError):
    """Raised when the local e2e workflow fails validation."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Submit a real local run and wait for the worker to complete it.")
    parser.add_argument("--spawn-services", action="store_true", help="Start the local API service and worker automatically.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for an already running backend service.")
    parser.add_argument("--poll-timeout", type=float, default=180.0, help="Seconds to wait for the evaluation to reach a terminal state.")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Seconds between evaluation detail polls.")
    return parser.parse_args()


def session_scope() -> Session:
    return SessionLocal()


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise E2ELocalRunError(message)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def check_envelope(response: httpx.Response, *, status_code: int) -> dict[str, Any]:
    ensure(
        response.status_code == status_code,
        f"{response.request.method} {response.request.url.path} expected {status_code}, got {response.status_code}: {response.text}",
    )
    payload = response.json()
    ensure(isinstance(payload, dict), "response must be a JSON object")
    ensure({"code", "data", "message"}.issubset(payload.keys()), "response must use {code, data, message}")
    return payload


def build_submission_payload(request_id: str, *, difficulty: float = 0.5) -> dict[str, Any]:
    return {
        "agentName": "local-e2e-agent",
        "description": "local worker e2e",
        "submitMethod": "api",
        "api": {
            "baseUrl": "https://example.com/agent",
        },
        "parameters": {
            "difficulty": difficulty,
            "timeoutMinutes": 20,
            "retryEnabled": False,
        },
        "publicToLeaderboard": False,
        "datasetIds": [DATASET_ID],
        "requestId": request_id,
    }


def is_terminal_run_status(status: str) -> bool:
    return status in RUN_TERMINAL_STATUSES


def count_active_samples(dataset_code: str) -> int:
    with session_scope() as session:
        rows = session.execute(
            select(BenchmarkSample.id)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(
                RiskSubtype.code == dataset_code,
                RiskSubtype.is_active.is_(True),
                BenchmarkSample.is_active.is_(True),
            )
        ).all()
    return len(rows)


def count_matching_samples_for_difficulty(dataset_code: str, difficulty: float) -> int:
    lower, upper, include_upper = difficulty_bucket_bounds(difficulty)
    with session_scope() as session:
        query = (
            select(BenchmarkSample.id)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(
                RiskSubtype.code == dataset_code,
                RiskSubtype.is_active.is_(True),
                BenchmarkSample.is_active.is_(True),
                BenchmarkSample.difficulty_score >= lower,
            )
        )
        if include_upper:
            query = query.where(BenchmarkSample.difficulty_score <= upper)
        else:
            query = query.where(BenchmarkSample.difficulty_score < upper)
        rows = session.execute(query).all()
    return len(rows)


def list_active_difficulty_scores(dataset_code: str) -> list[float]:
    with session_scope() as session:
        rows = session.execute(
            select(BenchmarkSample.difficulty_score)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(
                RiskSubtype.code == dataset_code,
                RiskSubtype.is_active.is_(True),
                BenchmarkSample.is_active.is_(True),
            )
            .distinct()
            .order_by(BenchmarkSample.difficulty_score.asc())
        ).scalars().all()
    return [float(value) for value in rows]


def resolve_submission_difficulty(dataset_code: str, preferred_difficulty: float) -> tuple[float, bool]:
    if count_matching_samples_for_difficulty(dataset_code, preferred_difficulty) > 0:
        return preferred_difficulty, False

    available_scores = list_active_difficulty_scores(dataset_code)
    ensure(available_scores, f"{dataset_code} has no active samples available for local e2e")
    fallback = min(available_scores, key=lambda value: (abs(value - preferred_difficulty), value))
    return fallback, True


def current_alembic_revision() -> str:
    with session_scope() as session:
        return str(session.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one())


def run_command(command: list[str], description: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=str(BACKEND_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise E2ELocalRunError(f"{description} failed with exit code {completed.returncode}: {detail}")
    return completed


def ensure_dataset_ready(dataset_code: str = DATASET_ID) -> int:
    current_count = count_active_samples(dataset_code)
    if current_count > 0:
        return current_count

    run_command(
        ["uv", "run", "python", "scripts/import_dataset_metadata.py"],
        "import dataset metadata",
    )
    run_command(
        [
            "uv",
            "run",
            "python",
            "scripts/import_dataset_samples.py",
            "--sample-root",
            "./data/02_Integrity/B2_Cloud_File_Modification",
            "--mode",
            "auto",
        ],
        "import B2 dataset samples",
    )

    current_count = count_active_samples(dataset_code)
    ensure(current_count > 0, f"{dataset_code} is still empty after bootstrap import")
    return current_count


def build_register_payload(prefix: str) -> dict[str, str]:
    return {
        "username": f"{prefix}_user",
        "email": f"{prefix}@example.com",
        "password": "secret123",
    }


def read_log_tail(path: Path, max_chars: int = 3000) -> str:
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="replace")
    return content[-max_chars:]


def start_service(name: str, command: list[str], log_path: Path) -> SpawnedService:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=str(BACKEND_ROOT),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return SpawnedService(name=name, process=process, log_path=log_path)


def stop_service(service: SpawnedService) -> None:
    if service.process.poll() is not None:
        return
    service.process.terminate()
    try:
        service.process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        service.process.kill()
        service.process.wait(timeout=5)


def service_log_dir() -> Path:
    directory = settings.runtime_root / "e2e_logs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def spawn_local_services(base_url: str) -> list[SpawnedService]:
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8000
    log_dir = service_log_dir()
    suffix = utc_timestamp()
    services = [
        start_service(
            "api",
            ["uv", "run", "uvicorn", "app.main:app", "--host", host, "--port", str(port)],
            log_dir / f"api_{suffix}.log",
        ),
        start_service(
            "worker",
            ["uv", "run", "python", "worker.py"],
            log_dir / f"worker_{suffix}.log",
        ),
    ]
    return services


def wait_for_api_ready(base_url: str, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=3.0) as client:
        while time.monotonic() < deadline:
            try:
                response = client.get("/api/v1/")
                payload = response.json()
                if response.status_code == 200 and payload.get("code") == 0:
                    return
            except Exception:
                pass
            time.sleep(0.5)
    raise E2ELocalRunError(f"API service did not become ready at {base_url.rstrip('/')}")


def poll_evaluation_detail(
    client: httpx.Client,
    evaluation_id: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
    headers: dict[str, str] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    deadline = time.monotonic() + timeout_seconds
    seen_statuses: list[str] = []
    last_payload: dict[str, Any] | None = None

    while time.monotonic() < deadline:
        detail = check_envelope(
            client.get(f"/api/v1/evaluations/{evaluation_id}", headers=headers),
            status_code=200,
        )["data"]
        status = str(detail["status"])
        if not seen_statuses or seen_statuses[-1] != status:
            seen_statuses.append(status)
        last_payload = detail
        if is_terminal_run_status(status):
            return detail, seen_statuses
        time.sleep(poll_interval_seconds)

    raise E2ELocalRunError(
        f"run remained pending/running too long: evaluationId={evaluation_id}, seenStatuses={seen_statuses}, "
        "please check the worker process and database connectivity"
    )


def collect_run_snapshot(evaluation_id: str) -> RunSnapshot:
    with session_scope() as session:
        run = session.execute(select(TestRun).where(TestRun.public_id == evaluation_id)).scalar_one_or_none()
        ensure(run is not None, f"run not found in database: {evaluation_id}")

        datasets = session.execute(select(RunDataset).where(RunDataset.run_id == run.id)).scalars().all()
        sample_executions = session.execute(select(SampleExecution).where(SampleExecution.run_id == run.id)).scalars().all()
        sample_execution_ids = [execution.id for execution in sample_executions]
        artifacts = []
        summaries = []
        if sample_execution_ids:
            artifacts = session.execute(
                select(ExecutionArtifact).where(ExecutionArtifact.sample_execution_id.in_(sample_execution_ids))
            ).scalars().all()
            summaries = session.execute(
                select(ExecutionSummary).where(ExecutionSummary.sample_execution_id.in_(sample_execution_ids))
            ).scalars().all()
        report = session.execute(select(RunReport).where(RunReport.run_id == run.id)).scalar_one_or_none()

    runtime_paths = [
        f"{execution.work_dir}/project/agent_runtime/runs/{execution.environment_ref}"
        for execution in sample_executions
        if execution.work_dir and execution.environment_ref
    ]
    return RunSnapshot(
        evaluation_id=evaluation_id,
        run_id=run.id,
        run_status=run.status,
        finalization_reason=run.finalization_reason,
        dataset_statuses={dataset.dataset_code: dataset.status for dataset in datasets},
        sample_statuses=[execution.status for execution in sample_executions],
        sample_errors=[execution.error_message for execution in sample_executions if execution.error_message],
        artifact_types={artifact.artifact_type for artifact in artifacts},
        final_labels={summary.final_label for summary in summaries if summary.final_label},
        report_summary=None if report is None else report.summary_json,
        runtime_paths=runtime_paths,
    )


def validate_run_snapshot(snapshot: RunSnapshot) -> None:
    ensure(
        snapshot.run_status == "completed",
        f"run did not complete successfully: status={snapshot.run_status}, finalizationReason={snapshot.finalization_reason}",
    )
    ensure(
        "done" in snapshot.sample_statuses,
        f"no sample execution finished with status=done, got {snapshot.sample_statuses}",
    )
    missing_artifacts = CORE_ARTIFACT_TYPES - snapshot.artifact_types
    ensure(
        not missing_artifacts,
        f"missing required artifact types: {sorted(missing_artifacts)} (present={sorted(snapshot.artifact_types)})",
    )
    invalid_labels = snapshot.final_labels - SUCCESS_LABELS
    ensure(
        not invalid_labels,
        f"unexpected execution summary labels: {sorted(invalid_labels)}",
    )
    ensure(snapshot.report_summary is not None, "run report summary is missing")
    ensure(bool(snapshot.report_summary), "run report summary is empty")


def print_summary(snapshot: RunSnapshot, seen_statuses: list[str]) -> None:
    print(
        json.dumps(
            {
                "evaluationId": snapshot.evaluation_id,
                "runId": snapshot.run_id,
                "runStatus": snapshot.run_status,
                "seenStatuses": seen_statuses,
                "datasetStatuses": snapshot.dataset_statuses,
                "sampleStatuses": snapshot.sample_statuses,
                "artifactTypes": sorted(snapshot.artifact_types),
                "finalLabels": sorted(snapshot.final_labels),
                "runtimePaths": snapshot.runtime_paths,
                "finalizationReason": snapshot.finalization_reason,
                "sampleErrors": snapshot.sample_errors,
                "reportSummary": snapshot.report_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> int:
    args = parse_args()
    if settings.WORKER_DISPATCH_MODE_DEFAULT != "synthetic_local":
        print(
            f"[warning] WORKER_DISPATCH_MODE_DEFAULT={settings.WORKER_DISPATCH_MODE_DEFAULT}; "
            "this e2e flow expects synthetic_local for automatic runtime closure.",
            file=sys.stderr,
        )

    base_url = args.base_url.rstrip("/")
    request_suffix = utc_timestamp()
    prefix = f"local_e2e_{request_suffix}"
    register_payload = build_register_payload(prefix)
    spawned_services: list[SpawnedService] = []

    try:
        revision = current_alembic_revision()
        print(f"[e2e_local_run] database ready, alembic revision={revision}")

        sample_count = ensure_dataset_ready(DATASET_ID)
        print(f"[e2e_local_run] dataset {DATASET_ID} ready with activeSamples={sample_count}")
        resolved_difficulty, adjusted = resolve_submission_difficulty(DATASET_ID, 0.5)
        if adjusted:
            print(
                f"[e2e_local_run] adjusted difficulty from 0.5 to {resolved_difficulty} "
                f"because the preferred bucket has no active {DATASET_ID} samples"
            )
        submission_payload = build_submission_payload(
            request_id=f"{prefix}_request",
            difficulty=resolved_difficulty,
        )

        if args.spawn_services:
            ensure(shutil.which("uv") is not None, "`uv` command is required for --spawn-services mode")
            spawned_services = spawn_local_services(base_url)
            wait_for_api_ready(base_url, timeout_seconds=20.0)
        else:
            wait_for_api_ready(base_url, timeout_seconds=10.0)

        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            register_response = check_envelope(client.post("/api/v1/auth/register", json=register_payload), status_code=200)
            token = register_response["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}

            submit_response = check_envelope(
                client.post("/api/v1/agents/submit", headers=headers, json=submission_payload),
                status_code=200,
            )
            ensure(submit_response["data"]["status"] == "pending", "submitted run must start from pending")
            evaluation_id = str(submit_response["data"]["evaluationId"])
            print(f"[e2e_local_run] submitted evaluationId={evaluation_id}")

            detail_payload, seen_statuses = poll_evaluation_detail(
                client,
                evaluation_id,
                timeout_seconds=args.poll_timeout,
                poll_interval_seconds=args.poll_interval,
                headers=headers,
            )

        ensure(
            "running" in seen_statuses or detail_payload["status"] == "running",
            f"run never observed in running state, seenStatuses={seen_statuses}",
        )

        snapshot = collect_run_snapshot(evaluation_id)
        if snapshot.run_status == "failed":
            print_summary(snapshot, seen_statuses)
            raise E2ELocalRunError(
                f"run failed: finalizationReason={snapshot.finalization_reason}, sampleErrors={snapshot.sample_errors}"
            )

        validate_run_snapshot(snapshot)
        print_summary(snapshot, seen_statuses)
        print(f"[e2e_local_run] local real run succeeded for {evaluation_id}")
        return 0
    except httpx.HTTPError as exc:
        print(f"[e2e_local_run] HTTP failure: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[e2e_local_run] failed: {exc}", file=sys.stderr)
        for service in spawned_services:
            tail = read_log_tail(service.log_path)
            if tail:
                print(f"[e2e_local_run] {service.name} log tail ({service.log_path}):\n{tail}", file=sys.stderr)
        return 1
    finally:
        for service in reversed(spawned_services):
            stop_service(service)
        SYNC_ENGINE.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
