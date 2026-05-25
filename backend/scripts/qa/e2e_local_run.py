"""运行本地端到端提交流程，并校验 worker 真正完成一轮执行。"""

from __future__ import annotations

import argparse
import getpass
import ipaddress
import json
import os
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
from sqlalchemy import delete, or_, select, text

# 允许通过 `python scripts/...` 直接执行时正确导入 backend 包内模块。
_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.models.agent import Agent
from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import (
    ExecutionArtifact,
    ExecutionSummary,
    OracleResult,
    RunDataset,
    RunReport,
    RunSample,
    RuntimeSession,
    SampleDifficultyStat,
    SampleExecution,
    TestRun,
)
from app.models.scoring import EvaluationScore, LeaderboardEntry
from app.models.user import User
from app.platform.config import settings
from app.platform.runtime_rules import difficulty_bucket_bounds
from app.platform.storage import default_credential_store
from scripts._common import BACKEND_CWD, build_sync_engine, build_sync_session_factory

DATASET_ID = "B2_cloud_file_modification"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
CORE_ARTIFACT_TYPES = {"event_log", "finalize_payload", "analysis_result"}
RUN_TERMINAL_STATUSES = {"completed", "terminated", "canceled", "failed"}
SUCCESS_LABELS = {"safe", "needs_review", "timeout"}
IMPORT_DATASET_METADATA_SCRIPT = "scripts/datasets/import_metadata.py"
IMPORT_DATASET_SAMPLES_SCRIPT = "scripts/datasets/import_samples.py"
DEFAULT_SAMPLE_ROOT = "./data/02_Integrity/B2_Cloud_File_Modification"
SUPPORTED_AGENT_TEMPLATE_IDS = ("http_submit_poll_basic", "skyvern_cloud_api")

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


@dataclass(slots=True)
class CleanupSummary:
    """Rows and credential files removed by local e2e cleanup."""

    users: int = 0
    agents: int = 0
    test_runs: int = 0
    run_datasets: int = 0
    run_samples: int = 0
    sample_executions: int = 0
    runtime_sessions: int = 0
    execution_artifacts: int = 0
    oracle_results: int = 0
    execution_summaries: int = 0
    run_reports: int = 0
    evaluation_scores: int = 0
    leaderboard_entries: int = 0
    credential_refs: int = 0

    def as_dict(self) -> dict[str, int]:
        """Return a JSON-friendly summary."""
        return {
            "users": self.users,
            "agents": self.agents,
            "testRuns": self.test_runs,
            "runDatasets": self.run_datasets,
            "runSamples": self.run_samples,
            "sampleExecutions": self.sample_executions,
            "runtimeSessions": self.runtime_sessions,
            "executionArtifacts": self.execution_artifacts,
            "oracleResults": self.oracle_results,
            "executionSummaries": self.execution_summaries,
            "runReports": self.run_reports,
            "evaluationScores": self.evaluation_scores,
            "leaderboardEntries": self.leaderboard_entries,
            "credentialRefs": self.credential_refs,
        }


@dataclass(slots=True)
class SampleDifficultyStatsSnapshot:
    """Snapshot of dataset-level sample difficulty stats before local e2e."""

    dataset_code: str
    sample_ids: list[int]
    rows: dict[int, dict[str, Any]]


class E2ELocalRunError(RuntimeError):
    """Raised when the local e2e workflow fails validation."""


def parse_args() -> argparse.Namespace:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Submit a real local run and wait for the worker to complete it."
    )
    parser.add_argument(
        "--spawn-services",
        action="store_true",
        help="Start the local API service and worker automatically.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base URL for an already running backend service.",
    )
    parser.add_argument(
        "--poll-timeout",
        type=float,
        default=180.0,
        help="Seconds to wait for the evaluation to reach a terminal state.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds between evaluation detail polls.",
    )
    parser.add_argument(
        "--dataset-id",
        default=DATASET_ID,
        help="Existing dataset code to use for the local e2e submission.",
    )
    parser.add_argument(
        "--difficulty",
        type=float,
        default=0.5,
        help="Preferred difficulty bucket to submit. Falls back when no active samples match.",
    )
    parser.add_argument(
        "--no-dataset-import",
        action="store_true",
        help="Fail if the selected dataset has no active samples instead of importing data.",
    )
    parser.add_argument(
        "--agent-base-url",
        default="https://agent.example.com",
        help="Base URL for the API Agent registered by this e2e run.",
    )
    parser.add_argument(
        "--agent-template-id",
        choices=SUPPORTED_AGENT_TEMPLATE_IDS,
        default="http_submit_poll_basic",
        help="Agent registration template shape to use for this e2e run.",
    )
    parser.add_argument(
        "--agent-api-key",
        default="",
        help="Optional API key used for api_key_header templates such as Skyvern cloud/local API.",
    )
    parser.add_argument(
        "--agent-api-key-stdin",
        action="store_true",
        help="Read the Agent API key from stdin instead of exposing it in process arguments.",
    )
    parser.add_argument(
        "--dispatch-mode",
        choices=["synthetic_local", "external_agent_api"],
        default="synthetic_local",
        help="Worker dispatch mode to validate after submission.",
    )
    parser.add_argument(
        "--spawn-mock-agent",
        action="store_true",
        help="Start a local mock Agent API and point the registered Agent at it.",
    )
    parser.add_argument(
        "--mock-agent-port",
        type=int,
        default=18081,
        help="Port used by --spawn-mock-agent.",
    )
    parser.add_argument(
        "--cleanup-created-records",
        action="store_true",
        help="Delete only the user, Agent, evaluation run graph, and credentials created by this local e2e invocation.",
    )
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
    ensure(
        {"code", "data", "message"}.issubset(payload.keys()),
        "response must use {code, data, message}",
    )
    return payload


def build_agent_payload(
    prefix: str,
    *,
    agent_base_url: str = "https://agent.example.com",
    agent_template_id: str = "http_submit_poll_basic",
    agent_api_key: str = "",
) -> dict[str, Any]:
    """构造本地 e2e 使用的 API Agent 注册请求体。"""
    if agent_template_id == "skyvern_cloud_api":
        auth = (
            {
                "type": "api_key_header",
                "config": {"headerName": "x-api-key", "secret": agent_api_key},
            }
            if agent_api_key
            else {"type": "none", "config": {}}
        )
        return {
            "templateId": "skyvern_cloud_api",
            "name": "local-e2e-skyvern-agent",
            "description": "local worker e2e via Skyvern API",
            "invokeMode": "submit_poll",
            "connection": {
                "baseUrl": agent_base_url,
                "invokePath": "/v1/run/tasks",
                "resultPathTemplate": "/v1/runs/{externalRunId}",
                "requestTimeoutSeconds": 60,
                "pollIntervalSeconds": 5,
                "pollTimeoutSeconds": 1800,
            },
            "auth": auth,
            "platformInputMapping": {
                "task": "prompt",
                "entryUrl": "url",
                "maxSteps": "max_steps",
            },
            "taskRenderMode": "goal_only",
            "customRequestBody": {"engine": "skyvern-2.0"},
            "requestOptions": {
                "structuredOutput": {
                    "supported": True,
                    "fieldAlias": "data_extraction_schema",
                }
            },
            "platformOutputMapping": {
                "externalRunId": "run_id",
                "status": "status",
                "finalAnswer": "output",
                "errorMessage": "failure_reason",
            },
            "terminalStatuses": [
                "completed",
                "failed",
                "timed_out",
                "terminated",
                "canceled",
            ],
            "successStatuses": ["completed"],
        }

    if agent_template_id != "http_submit_poll_basic":
        raise E2ELocalRunError(f"unsupported agent template: {agent_template_id}")

    return {
        "templateId": "http_submit_poll_basic",
        "name": "local-e2e-agent",
        "description": "local worker e2e",
        "invokeMode": "sync_response",
        "connection": {
            "baseUrl": agent_base_url,
            "invokePath": "/run",
            "requestTimeoutSeconds": 30,
        },
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
        "platformOutputMapping": {
            "status": "status",
            "finalAnswer": "answer",
            "errorMessage": "error",
        },
        "terminalStatuses": ["completed", "failed"],
        "successStatuses": ["completed"],
    }


def build_submission_payload(
    request_id: str,
    *,
    agent_id: str = "agt_local_e2e",
    dataset_id: str = DATASET_ID,
    difficulty: float = 0.5,
) -> dict[str, Any]:
    """构造本地 e2e 用的标准提交请求体。"""
    return {
        "submitMethod": "api",
        "agentId": agent_id,
        "parameters": {
            "difficulty": difficulty,
            "timeoutMinutes": 20,
            "maxSteps": 30,
        },
        "leaderboardDisplayMode": "anonymous",
        "datasetIds": [dataset_id],
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
        rows = (
            session.execute(
                select(BenchmarkSample.difficulty_score)
                .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
                .where(
                    RiskSubtype.code == dataset_code,
                    RiskSubtype.is_active.is_(True),
                    BenchmarkSample.is_active.is_(True),
                )
                .distinct()
                .order_by(BenchmarkSample.difficulty_score.asc())
            )
            .scalars()
            .all()
        )
    return [float(value) for value in rows]


def resolve_submission_difficulty(
    dataset_code: str, preferred_difficulty: float
) -> tuple[float, bool]:
    """优先使用期望难度；没有样本时回退到最接近的可用分值。"""
    if count_matching_samples_for_difficulty(dataset_code, preferred_difficulty) > 0:
        return preferred_difficulty, False

    available_scores = list_active_difficulty_scores(dataset_code)
    ensure(
        bool(available_scores),
        f"{dataset_code} has no active samples available for local e2e",
    )
    fallback = min(
        available_scores, key=lambda value: (abs(value - preferred_difficulty), value)
    )
    return fallback, True


def current_alembic_revision() -> str:
    """读取当前数据库的 Alembic 版本号，便于诊断环境状态。"""
    with session_scope() as session:
        return str(
            session.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            ).scalar_one()
        )


def run_command(
    command: list[str], description: str
) -> subprocess.CompletedProcess[str]:
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
        raise E2ELocalRunError(
            f"{description} failed with exit code {completed.returncode}: {detail}"
        )
    return completed


def resolve_effective_agent_base_url(args: argparse.Namespace) -> str:
    """Resolve the Agent base URL that will be stored in the registered Agent."""
    if bool(args.spawn_mock_agent):
        return f"http://127.0.0.1:{int(args.mock_agent_port)}"
    return str(args.agent_base_url)


def resolve_agent_api_key(args: argparse.Namespace) -> str:
    """Resolve the optional Agent API key without requiring command-line exposure."""
    if bool(getattr(args, "agent_api_key_stdin", False)):
        if sys.stdin.isatty():
            return getpass.getpass(prompt="").strip()
        return sys.stdin.readline().strip()
    return str(args.agent_api_key or "")


def build_service_env(*, allow_private_agent_networks: bool = False) -> dict[str, str]:
    """Build child-process environment for API/worker services."""
    env = dict(os.environ)
    if allow_private_agent_networks:
        env["AGENT_HTTP_ALLOW_PRIVATE_NETWORKS"] = "true"
    return env


def agent_base_url_requires_private_network_access(agent_base_url: str) -> bool:
    """Return whether a local e2e Agent URL needs private-network allowance."""
    parsed = urlparse(agent_base_url)
    hostname = parsed.hostname
    if not hostname:
        return False
    if hostname.lower() == "localhost":
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return bool(address.is_private or address.is_loopback or address.is_link_local)


def ensure_dataset_ready(
    dataset_code: str = DATASET_ID, *, allow_import: bool = True
) -> int:
    """确保 e2e 所需数据集已入库；为空时自动执行导入脚本。"""
    current_count = count_active_samples(dataset_code)
    if current_count > 0:
        return current_count

    if not allow_import:
        raise E2ELocalRunError(
            f"{dataset_code} has no active samples and dataset import is disabled"
        )

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
        agent = session.execute(
            select(Agent).where(Agent.public_id == agent_id)
        ).scalar_one()
        agent.status = "active"
        session.commit()


def force_synthetic_dispatch(evaluation_id: str) -> None:
    """本地 e2e 继续复用 synthetic runtime 闭环，不依赖外部 Agent 服务。"""
    with session_scope() as session:
        run = session.execute(
            select(TestRun).where(TestRun.public_id == evaluation_id)
        ).scalar_one()
        config = dict(run.execution_config or {})
        config["dispatch"] = {"mode": "synthetic_local"}
        run.execution_config = config
        session.commit()


def _rowcount(result: Any) -> int:
    """Normalize SQLAlchemy rowcount values for cleanup summaries."""
    value = getattr(result, "rowcount", 0)
    return int(value or 0)


def cleanup_created_records(
    prefix: str,
    *,
    evaluation_id: str | None = None,
    agent_id: str | None = None,
) -> CleanupSummary:
    """Delete only records created by this local e2e script invocation."""
    if not prefix.startswith("local_e2e_"):
        raise E2ELocalRunError(
            f"cleanup refuses to clean non-local-e2e prefix: {prefix}"
        )

    summary = CleanupSummary()
    credential_store = default_credential_store()
    with session_scope() as session:
        user_ids = list(
            (
                session.execute(
                    select(User.id).where(
                        or_(
                            User.username == f"{prefix}_user",
                            User.email == f"{prefix}@example.com",
                        )
                    )
                )
            ).scalars()
        )

        run_filters = []
        if evaluation_id:
            run_filters.append(TestRun.public_id == evaluation_id)
        if user_ids:
            run_filters.append(TestRun.user_id.in_(user_ids))
        run_ids: list[int] = []
        if run_filters:
            run_ids = list(
                (
                    session.execute(
                        select(TestRun.id).where(or_(*run_filters))
                    )
                ).scalars()
            )

        agent_filters = []
        if agent_id:
            agent_filters.append(Agent.public_id == agent_id)
        if user_ids:
            agent_filters.append(Agent.user_id.in_(user_ids))
        agent_rows: list[tuple[int, str | None]] = []
        if agent_filters:
            agent_rows = list(
                session.execute(
                    select(Agent.id, Agent.credential_ref).where(or_(*agent_filters))
                )
            )
        agent_ids = [row[0] for row in agent_rows]

        run_credential_refs: list[str | None] = []
        if run_ids:
            run_credential_refs = list(
                (
                    session.execute(
                        select(TestRun.credential_ref).where(TestRun.id.in_(run_ids))
                    )
                ).scalars()
            )
        credential_refs = {
            credential_ref
            for credential_ref in [
                *(row[1] for row in agent_rows),
                *run_credential_refs,
            ]
            if credential_ref
        }

        sample_execution_ids: list[int] = []
        score_ids: list[int] = []
        if run_ids:
            sample_execution_ids = list(
                (
                    session.execute(
                        select(SampleExecution.id).where(
                            SampleExecution.run_id.in_(run_ids)
                        )
                    )
                ).scalars()
            )
            score_ids = list(
                (
                    session.execute(
                        select(EvaluationScore.id).where(
                            EvaluationScore.run_id.in_(run_ids)
                        )
                    )
                ).scalars()
            )

            if score_ids:
                summary.leaderboard_entries += _rowcount(
                    session.execute(
                        delete(LeaderboardEntry).where(
                            LeaderboardEntry.score_id.in_(score_ids)
                        )
                    )
                )
            summary.leaderboard_entries += _rowcount(
                session.execute(
                    delete(LeaderboardEntry).where(
                        LeaderboardEntry.run_id.in_(run_ids)
                    )
                )
            )
            summary.evaluation_scores += _rowcount(
                session.execute(
                    delete(EvaluationScore).where(EvaluationScore.run_id.in_(run_ids))
                )
            )
            summary.run_reports += _rowcount(
                session.execute(delete(RunReport).where(RunReport.run_id.in_(run_ids)))
            )

        if sample_execution_ids:
            summary.runtime_sessions += _rowcount(
                session.execute(
                    delete(RuntimeSession).where(
                        RuntimeSession.sample_execution_id.in_(sample_execution_ids)
                    )
                )
            )
            summary.execution_artifacts += _rowcount(
                session.execute(
                    delete(ExecutionArtifact).where(
                        ExecutionArtifact.sample_execution_id.in_(sample_execution_ids)
                    )
                )
            )
            summary.oracle_results += _rowcount(
                session.execute(
                    delete(OracleResult).where(
                        OracleResult.sample_execution_id.in_(sample_execution_ids)
                    )
                )
            )
            summary.execution_summaries += _rowcount(
                session.execute(
                    delete(ExecutionSummary).where(
                        ExecutionSummary.sample_execution_id.in_(sample_execution_ids)
                    )
                )
            )
            summary.sample_executions += _rowcount(
                session.execute(
                    delete(SampleExecution).where(
                        SampleExecution.id.in_(sample_execution_ids)
                    )
                )
            )

        if run_ids:
            summary.run_samples += _rowcount(
                session.execute(delete(RunSample).where(RunSample.run_id.in_(run_ids)))
            )
            summary.run_datasets += _rowcount(
                session.execute(
                    delete(RunDataset).where(RunDataset.run_id.in_(run_ids))
                )
            )
            summary.test_runs += _rowcount(
                session.execute(delete(TestRun).where(TestRun.id.in_(run_ids)))
            )

        if agent_ids:
            summary.agents += _rowcount(
                session.execute(delete(Agent).where(Agent.id.in_(agent_ids)))
            )
        if user_ids:
            summary.users += _rowcount(
                session.execute(delete(User).where(User.id.in_(user_ids)))
            )

        session.commit()

    for credential_ref in credential_refs:
        credential_store.delete(credential_ref)
        summary.credential_refs += 1
    return summary


SAMPLE_DIFFICULTY_STAT_FIELDS = (
    "sample_id_ref",
    "valid_execution_count",
    "completed_count",
    "unfinished_count",
    "harm_count",
    "safe_completion_count",
    "minor_harm_count",
    "major_harm_count",
    "critical_harm_count",
    "harm_rate",
    "safe_completion_rate",
    "inferred_difficulty",
    "candidate_completion_difficulty",
    "candidate_safety_difficulty",
    "candidate_difficulty_score",
    "algorithm_version",
    "last_execution_at",
    "updated_at",
)


def snapshot_sample_difficulty_stats(dataset_code: str) -> SampleDifficultyStatsSnapshot:
    """Capture mutable sample difficulty stats for an existing dataset."""
    with session_scope() as session:
        sample_ids = list(
            (
                session.execute(
                    select(BenchmarkSample.id)
                    .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
                    .where(RiskSubtype.code == dataset_code)
                )
            ).scalars()
        )
        rows: dict[int, dict[str, Any]] = {}
        if sample_ids:
            stats = (
                session.execute(
                    select(SampleDifficultyStat).where(
                        SampleDifficultyStat.sample_id_ref.in_(sample_ids)
                    )
                )
                .scalars()
                .all()
            )
            rows = {
                int(stat.sample_id_ref): {
                    field: getattr(stat, field)
                    for field in SAMPLE_DIFFICULTY_STAT_FIELDS
                }
                for stat in stats
            }
    return SampleDifficultyStatsSnapshot(
        dataset_code=dataset_code, sample_ids=sample_ids, rows=rows
    )


def restore_sample_difficulty_stats(
    snapshot: SampleDifficultyStatsSnapshot,
) -> dict[str, int]:
    """Restore mutable sample difficulty stats after local e2e use of a dataset."""
    if not snapshot.sample_ids:
        return {"deleted": 0, "restored": 0}

    with session_scope() as session:
        deleted = _rowcount(
            session.execute(
                delete(SampleDifficultyStat).where(
                    SampleDifficultyStat.sample_id_ref.in_(snapshot.sample_ids)
                )
            )
        )
        for row in snapshot.rows.values():
            session.add(SampleDifficultyStat(**row))
        session.commit()

    return {"deleted": deleted, "restored": len(snapshot.rows)}


def read_log_tail(path: Path, max_chars: int = 3000) -> str:
    """读取日志尾部，便于失败时快速定位原因。"""
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="replace")
    return content[-max_chars:]


def start_service(
    name: str,
    command: list[str],
    log_path: Path,
    *,
    env: dict[str, str] | None = None,
) -> SpawnedService:
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
        env=env,
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


def spawn_local_services(
    base_url: str, *, allow_private_agent_networks: bool = False
) -> list[SpawnedService]:
    """按 base URL 派生 host/port，并同时启动 API 与 worker。"""
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8000
    log_dir = service_log_dir()
    suffix = utc_timestamp()
    env = build_service_env(
        allow_private_agent_networks=allow_private_agent_networks
    )
    services = [
        start_service(
            "api",
            [
                "uv",
                "run",
                "uvicorn",
                "app.main:app",
                "--host",
                host,
                "--port",
                str(port),
            ],
            log_dir / f"api_{suffix}.log",
            env=env,
        ),
        start_service(
            "worker",
            ["uv", "run", "python", "worker.py"],
            log_dir / f"worker_{suffix}.log",
            env=env,
        ),
    ]
    return services


def spawn_mock_agent_service(port: int) -> SpawnedService:
    """Start the local mock Agent API used by external_agent_api e2e runs."""
    log_dir = service_log_dir()
    suffix = utc_timestamp()
    return start_service(
        "mock-agent",
        [
            "uv",
            "run",
            "uvicorn",
            "scripts.qa.mock_agent_api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        log_dir / f"mock_agent_{suffix}.log",
    )


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
    raise E2ELocalRunError(
        f"API service did not become ready at {base_url.rstrip('/')}"
    )


def wait_for_mock_agent_ready(base_url: str, timeout_seconds: float) -> None:
    """Wait until the local mock Agent API is ready."""
    deadline = time.monotonic() + timeout_seconds
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=3.0) as client:
        while time.monotonic() < deadline:
            try:
                response = client.get("/health")
                payload = response.json()
                if response.status_code == 200 and payload.get("ok") is True:
                    return
            except Exception:
                pass
            time.sleep(0.5)
    raise E2ELocalRunError(
        f"mock Agent service did not become ready at {base_url.rstrip('/')}"
    )


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
        run = session.execute(
            select(TestRun).where(TestRun.public_id == evaluation_id)
        ).scalar_one_or_none()
        ensure(run is not None, f"run not found in database: {evaluation_id}")
        assert run is not None

        datasets = (
            session.execute(select(RunDataset).where(RunDataset.run_id == run.id))
            .scalars()
            .all()
        )
        sample_executions = (
            session.execute(
                select(SampleExecution).where(SampleExecution.run_id == run.id)
            )
            .scalars()
            .all()
        )
        sample_execution_ids = [execution.id for execution in sample_executions]
        artifacts = []
        summaries = []
        if sample_execution_ids:
            artifacts = (
                session.execute(
                    select(ExecutionArtifact).where(
                        ExecutionArtifact.sample_execution_id.in_(sample_execution_ids)
                    )
                )
                .scalars()
                .all()
            )
            summaries = (
                session.execute(
                    select(ExecutionSummary).where(
                        ExecutionSummary.sample_execution_id.in_(sample_execution_ids)
                    )
                )
                .scalars()
                .all()
            )
        report = session.execute(
            select(RunReport).where(RunReport.run_id == run.id)
        ).scalar_one_or_none()

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
        sample_errors=[
            execution.error_message
            for execution in sample_executions
            if execution.error_message
        ],
        artifact_types={artifact.artifact_type for artifact in artifacts},
        final_labels={
            summary.final_label for summary in summaries if summary.final_label
        },
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


def validate_observed_status_progress(
    seen_statuses: list[str], terminal_status: str
) -> None:
    """Accept fast runs that reach a terminal state between polling intervals."""
    if is_terminal_run_status(terminal_status):
        return
    raise E2ELocalRunError(
        f"run never reached a terminal state, seenStatuses={seen_statuses}"
    )


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
    if (
        args.dispatch_mode == "synthetic_local"
        and settings.WORKER_DISPATCH_MODE_DEFAULT != "synthetic_local"
    ):
        print(
            f"[warning] WORKER_DISPATCH_MODE_DEFAULT={settings.WORKER_DISPATCH_MODE_DEFAULT}; "
            "this e2e flow expects synthetic_local for automatic runtime closure.",
            file=sys.stderr,
        )

    base_url = args.base_url.rstrip("/")
    agent_base_url = resolve_effective_agent_base_url(args)
    agent_api_key = resolve_agent_api_key(args)
    allow_private_agent_networks = agent_base_url_requires_private_network_access(
        agent_base_url
    )
    request_suffix = utc_timestamp()
    prefix = f"local_e2e_{request_suffix}"
    register_payload = build_register_payload(prefix)
    spawned_services: list[SpawnedService] = []
    agent_id: str | None = None
    evaluation_id: str | None = None
    difficulty_stats_snapshot: SampleDifficultyStatsSnapshot | None = None

    try:
        revision = current_alembic_revision()
        print(f"[e2e_local_run] database ready, alembic revision={revision}")

        # 提交前先确保基础数据存在，否则无法创建可执行的评测任务。
        dataset_id = str(args.dataset_id)
        sample_count = ensure_dataset_ready(
            dataset_id, allow_import=not args.no_dataset_import
        )
        difficulty_stats_snapshot = snapshot_sample_difficulty_stats(dataset_id)
        print(
            f"[e2e_local_run] dataset {dataset_id} ready with activeSamples={sample_count}"
        )
        preferred_difficulty = float(args.difficulty)
        resolved_difficulty, adjusted = resolve_submission_difficulty(
            dataset_id, preferred_difficulty
        )
        if adjusted:
            print(
                f"[e2e_local_run] adjusted difficulty from {preferred_difficulty} to {resolved_difficulty} "
                f"because the preferred bucket has no active {dataset_id} samples"
            )
        submission_payload = build_submission_payload(
            request_id=f"{prefix}_request",
            dataset_id=dataset_id,
            difficulty=resolved_difficulty,
        )

        if args.spawn_mock_agent:
            mock_service = spawn_mock_agent_service(int(args.mock_agent_port))
            spawned_services.append(mock_service)
            wait_for_mock_agent_ready(agent_base_url, timeout_seconds=20.0)

        if args.spawn_services:
            ensure(
                shutil.which("uv") is not None,
                "`uv` command is required for --spawn-services mode",
            )
            spawned_services.extend(
                spawn_local_services(
                    base_url,
                    allow_private_agent_networks=allow_private_agent_networks,
                )
            )
            wait_for_api_ready(base_url, timeout_seconds=20.0)
        else:
            wait_for_api_ready(base_url, timeout_seconds=10.0)

        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            # 先注册一个独立测试账号，再走真实提交链路。
            register_response = check_envelope(
                client.post("/api/v1/auth/register", json=register_payload),
                status_code=200,
            )
            token = register_response["data"]["token"]
            headers = {"Authorization": f"Bearer {token}"}

            create_agent = check_envelope(
                client.post(
                    "/api/v1/agents",
                    headers=headers,
                    json=build_agent_payload(
                        prefix,
                        agent_base_url=agent_base_url,
                        agent_template_id=str(args.agent_template_id),
                        agent_api_key=agent_api_key,
                    ),
                ),
                status_code=200,
            )
            agent_id = str(create_agent["data"]["agentId"])
            mark_agent_active(agent_id)
            submission_payload["agentId"] = agent_id

            submit_response = check_envelope(
                client.post(
                    "/api/v1/evaluations", headers=headers, json=submission_payload
                ),
                status_code=200,
            )
            ensure(
                submit_response["data"]["status"] == "pending",
                "submitted run must start from pending",
            )
            evaluation_id = str(submit_response["data"]["evaluationId"])
            if args.dispatch_mode == "synthetic_local":
                force_synthetic_dispatch(evaluation_id)
            print(
                f"[e2e_local_run] submitted evaluationId={evaluation_id}, "
                f"dispatchMode={args.dispatch_mode}"
            )

            detail_payload, seen_statuses = poll_evaluation_detail(
                client,
                evaluation_id,
                timeout_seconds=args.poll_timeout,
                poll_interval_seconds=args.poll_interval,
                headers=headers,
            )

        validate_observed_status_progress(
            seen_statuses, str(detail_payload["status"])
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
                print(
                    f"[e2e_local_run] {service.name} log tail ({service.log_path}):\n{tail}",
                    file=sys.stderr,
                )
        return 1
    finally:
        for service in reversed(spawned_services):
            stop_service(service)
        if difficulty_stats_snapshot is not None:
            try:
                restore_summary = restore_sample_difficulty_stats(
                    difficulty_stats_snapshot
                )
                print(
                    "[e2e_local_run] sample difficulty stats restored: "
                    + json.dumps(
                        restore_summary,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                )
            except Exception as exc:
                print(
                    f"[e2e_local_run] sample difficulty stats restore failed: {exc}",
                    file=sys.stderr,
                )
        if args.cleanup_created_records:
            try:
                cleanup_summary = cleanup_created_records(
                    prefix,
                    evaluation_id=evaluation_id,
                    agent_id=agent_id,
                )
                print(
                    "[e2e_local_run] cleanup summary: "
                    + json.dumps(
                        cleanup_summary.as_dict(),
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                )
            except Exception as exc:
                print(f"[e2e_local_run] cleanup failed: {exc}", file=sys.stderr)
        SYNC_ENGINE.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
