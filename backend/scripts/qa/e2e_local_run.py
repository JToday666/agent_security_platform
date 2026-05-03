"""运行本地端到端提交流程，并校验 worker 真正完成一轮执行。"""

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
from sqlalchemy import select, text

# 允许通过 `python scripts/...` 直接执行时正确导入 backend 包内模块。
_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.models.agent import Agent
from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import ExecutionArtifact, ExecutionSummary, RunDataset, RunReport, SampleExecution, TestRun
from app.platform.config import settings
from app.platform.runtime_rules import difficulty_bucket_bounds
from scripts._common import BACKEND_CWD, build_sync_engine, build_sync_session_factory


DATASET_ID = "B2_cloud_file_modification"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
CORE_ARTIFACT_TYPES = {"event_log", "finalize_payload", "analysis_result"}
RUN_TERMINAL_STATUSES = {"completed", "terminated", "canceled", "failed"}
SUCCESS_LABELS = {"needs_review", "timeout"}
IMPORT_DATASET_METADATA_SCRIPT = "scripts/datasets/import_metadata.py"
IMPORT_DATASET_SAMPLES_SCRIPT = "scripts/datasets/import_samples.py"
DEFAULT_SAMPLE_ROOT = "./data/02_Integrity/B2_Cloud_File_Modification"

SYNC_ENGINE = build_sync_engine()
SessionLocal = build_sync_session_factory(SYNC_ENGINE)


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
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="Submit a real local run and wait for the worker to complete it.")
    parser.add_argument("--spawn-services", action="store_true", help="Start the local API service and worker automatically.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for an already running backend service.")
    parser.add_argument("--poll-timeout", type=float, default=180.0, help="Seconds to wait for the evaluation to reach a terminal state.")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Seconds between evaluation detail polls.")
    return parser.parse_args()


def session_scope():
    """返回脚本复用的同步 Session。"""
    return SessionLocal()


def ensure(condition: bool, message: str) -> None:
    """把断言失败统一提升为脚本级异常。"""
    if not condition:
        raise E2ELocalRunError(message)


def utc_timestamp() -> str:
    """生成用于请求号、日志文件名的 UTC 时间戳。"""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def check_envelope(response: httpx.Response, *, status_code: int) -> dict[str, Any]:
    """校验接口是否符合统一 envelope 结构。"""
    ensure(
        response.status_code == status_code,
        f"{response.request.method} {response.request.url.path} expected {status_code}, got {response.status_code}: {response.text}",
    )
    payload = response.json()
    ensure(isinstance(payload, dict), "response must be a JSON object")
    ensure({"code", "data", "message"}.issubset(payload.keys()), "response must use {code, data, message}")
    return payload


def build_agent_payload(prefix: str) -> dict[str, Any]:
    """构造本地 e2e 使用的 API Agent 注册请求体。"""
    return {
        "templateId": "http_submit_poll_basic",
        "name": "local-e2e-agent",
        "description": "local worker e2e",
        "invokeMode": "sync_response",
        "connection": {"baseUrl": "https://agent.example.com", "invokePath": "/run", "requestTimeoutSeconds": 30},
        "auth": {"type": "bearer", "config": {"token": f"sk-{prefix}"}},
        "platformInputMapping": {
            "task": "prompt",
            "entryUrl": "url",
            "timeoutSeconds": "timeout_sec",
            "sampleId": "sample_id",
            "evaluationId": "evaluation_id",
            "maxSteps": "max_steps",
        },
        "taskRenderMode": "goal_only",
        "customRequestBody": {"engine": "local-e2e"},
        "requestOptions": {},
        "platformOutputMapping": {"status": "status", "finalAnswer": "answer", "errorMessage": "error"},
        "terminalStatuses": ["completed", "failed"],
        "successStatuses": ["completed"],
    }


def build_submission_payload(request_id: str, *, agent_id: str = "agt_local_e2e", difficulty: float = 0.5) -> dict[str, Any]:
    """构造本地 e2e 用的标准提交请求体。"""
    return {
        "submitMethod": "api",
        "agentId": agent_id,
        "parameters": {
            "difficulty": difficulty,
            "timeoutMinutes": 20,
            "maxSteps": 30,
        },
        "publicToLeaderboard": False,
        "datasetIds": [DATASET_ID],
        "requestId": request_id,
    }


def is_terminal_run_status(status: str) -> bool:
    """判断评测任务是否已经进入终态。"""
    return status in RUN_TERMINAL_STATUSES


def count_active_samples(dataset_code: str) -> int:
    """统计指定数据集当前可用的激活样本数。"""
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
    """统计某个难度桶内可匹配的激活样本数。"""
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
    """列出指定数据集当前可用的去重难度分值。"""
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
    """优先使用期望难度；没有样本时回退到最接近的可用分值。"""
    if count_matching_samples_for_difficulty(dataset_code, preferred_difficulty) > 0:
        return preferred_difficulty, False

    available_scores = list_active_difficulty_scores(dataset_code)
    ensure(available_scores, f"{dataset_code} has no active samples available for local e2e")
    fallback = min(available_scores, key=lambda value: (abs(value - preferred_difficulty), value))
    return fallback, True


def current_alembic_revision() -> str:
    """读取当前数据库的 Alembic 版本号，便于诊断环境状态。"""
    with session_scope() as session:
        return str(session.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one())


def run_command(command: list[str], description: str) -> subprocess.CompletedProcess[str]:
    """在 backend 根目录执行外部命令，并把失败转成可读异常。"""
    completed = subprocess.run(
        command,
        cwd=BACKEND_CWD,
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
    """确保 e2e 所需数据集已入库；为空时自动执行导入脚本。"""
    current_count = count_active_samples(dataset_code)
    if current_count > 0:
        return current_count

    run_command(
        ["uv", "run", "python", IMPORT_DATASET_METADATA_SCRIPT],
        "import dataset metadata",
    )
    run_command(
        [
            "uv",
            "run",
            "python",
            IMPORT_DATASET_SAMPLES_SCRIPT,
            "--sample-root",
            DEFAULT_SAMPLE_ROOT,
            "--mode",
            "auto",
        ],
        "import B2 dataset samples",
    )

    current_count = count_active_samples(dataset_code)
    ensure(current_count > 0, f"{dataset_code} is still empty after bootstrap import")
    return current_count


def build_register_payload(prefix: str) -> dict[str, str]:
    """生成唯一用户名邮箱，避免本地多次执行时冲突。"""
    return {
        "username": f"{prefix}_user",
        "email": f"{prefix}@example.com",
        "password": "secret123",
    }


def mark_agent_active(agent_id: str) -> None:
    """本地 e2e 使用 DB 夹具方式跳过真实外部 Agent 验证。"""
    with session_scope() as session:
        agent = session.execute(select(Agent).where(Agent.public_id == agent_id)).scalar_one()
        agent.status = "active"
        session.commit()


def force_synthetic_dispatch(evaluation_id: str) -> None:
    """本地 e2e 继续复用 synthetic runtime 闭环，不依赖外部 Agent 服务。"""
    with session_scope() as session:
        run = session.execute(select(TestRun).where(TestRun.public_id == evaluation_id)).scalar_one()
        config = dict(run.execution_config or {})
        config["dispatch"] = {"mode": "synthetic_local"}
        run.execution_config = config
        session.commit()


def read_log_tail(path: Path, max_chars: int = 3000) -> str:
    """读取日志尾部，便于失败时快速定位原因。"""
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="replace")
    return content[-max_chars:]


def start_service(name: str, command: list[str], log_path: Path) -> SpawnedService:
    """启动本地服务进程并把输出重定向到日志文件。"""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=BACKEND_CWD,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return SpawnedService(name=name, process=process, log_path=log_path)


def stop_service(service: SpawnedService) -> None:
    """尽量优雅地关闭脚本拉起的子进程。"""
    if service.process.poll() is not None:
        return
    service.process.terminate()
    try:
        service.process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        service.process.kill()
        service.process.wait(timeout=5)


def service_log_dir() -> Path:
    """返回本地 e2e 服务日志目录。"""
    directory = settings.runtime_root / "e2e_logs"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def spawn_local_services(base_url: str) -> list[SpawnedService]:
    """按 base URL 派生 host/port，并同时启动 API 与 worker。"""
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
    """轮询版本根接口，直到 API 服务真正可用。"""
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
    """轮询评测详情接口，直到任务进入终态并返回状态轨迹。"""
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
    """从数据库收集执行快照，便于统一校验产物与状态。"""
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
    """校验运行结果是否满足本地 e2e 的最低成功标准。"""
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
    """打印便于排障的执行摘要。"""
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
    """串起数据准备、服务探活、提交流程与结果校验。"""
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

        # 提交前先确保基础数据存在，否则无法创建可执行的评测任务。
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
            # 先注册一个独立测试账号，再走真实提交链路。
            register_response = check_envelope(client.post("/api/v1/auth/register", json=register_payload), status_code=200)
            token = register_response["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}

            create_agent = check_envelope(client.post("/api/v1/agents", headers=headers, json=build_agent_payload(prefix)), status_code=200)
            agent_id = str(create_agent["data"]["agentId"])
            mark_agent_active(agent_id)
            submission_payload["agentId"] = agent_id

            submit_response = check_envelope(
                client.post("/api/v1/evaluations", headers=headers, json=submission_payload),
                status_code=200,
            )
            ensure(submit_response["data"]["status"] == "pending", "submitted run must start from pending")
            evaluation_id = str(submit_response["data"]["evaluationId"])
            force_synthetic_dispatch(evaluation_id)
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

        # HTTP 返回成功后，再回到数据库核对执行产物是否齐全。
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
