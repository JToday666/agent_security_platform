"""Run one real Skyvern-backed sample execution for evaluator validation."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_ROOT))

from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import (
    ExecutionArtifact,
    ExecutionSummary,
    OracleResult,
    RunDataset,
    RunSample,
    SampleDifficultyStat,
    SampleExecution,
    TestRun,
)
from app.models.user import User
from app.modules.evaluations.application.ids import generate_public_id
from app.modules.evaluations.lifecycle import finalize_run
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal
from app.platform.storage import default_credential_store
from app.worker.execution import execute_sample
from app.worker.execution_jobs import SampleJob
from app.worker.runtime import SampleRuntimeTarget


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and execute one local Skyvern sample without releasing it to the scheduler."
    )
    parser.add_argument("--sample-id", default="Browser-art_E1_1")
    parser.add_argument("--skyvern-base-url", default="http://127.0.0.1:18100")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument("--poll-interval-seconds", type=float, default=2.0)
    parser.add_argument("--poll-timeout-seconds", type=int, default=900)
    parser.add_argument("--skyvern-api-key-env", default="SKYVERN_API_KEY")
    parser.add_argument("--skyvern-engine", default="skyvern-2.0")
    parser.add_argument("--task-render-mode", default="goal_only")
    return parser.parse_args()


def build_skyvern_snapshot(
    args: argparse.Namespace, *, credential_ref: str | None = None
) -> dict[str, object]:
    auth: dict[str, object]
    if credential_ref:
        auth = {
            "type": "api_key_header",
            "headerName": "x-api-key",
            "credentialRef": credential_ref,
        }
    else:
        auth = {"type": "none", "config": {}, "credentialRef": None}
    return {
        "agentId": f"agt_skyvern_{uuid4().hex[:8]}",
        "templateId": "skyvern_cloud_api",
        "name": "qa-local-skyvern",
        "description": "Direct local Skyvern evaluator validation",
        "invokeMode": "submit_poll",
        "maxConcurrency": 1,
        "connection": {
            "baseUrl": args.skyvern_base_url.rstrip("/"),
            "invokePath": "/v1/run/tasks",
            "resultPathTemplate": "/v1/runs/{externalRunId}",
            "cancelPathTemplate": "/v1/runs/{externalRunId}/cancel",
            "cancelMethod": "POST",
            "cancelRequestBody": None,
            "requestTimeoutSeconds": 60,
            "pollIntervalSeconds": args.poll_interval_seconds,
            "pollTimeoutSeconds": args.poll_timeout_seconds,
        },
        "auth": auth,
        "platformInputMapping": {
            "task": "prompt",
            "browserEntryUrl": "url",
            "maxSteps": "max_steps",
        },
        "taskRenderMode": str(getattr(args, "task_render_mode", "goal_only")),
        "customRequestBody": {
            "engine": str(getattr(args, "skyvern_engine", "skyvern-2.0"))
        },
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


def build_execution_config(
    *,
    frozen_agent_snapshot: dict[str, object],
    evaluation_id: str | None,
    max_steps: int,
) -> dict[str, object]:
    return {
        "frozenAgentSnapshot": frozen_agent_snapshot,
        "evaluationId": evaluation_id,
        "maxSteps": max_steps,
        "parameters": {"retryEnabled": False},
    }


def build_run_execution_config(
    *,
    frozen_agent_snapshot: dict[str, object],
    evaluation_id: str | None,
    max_steps: int,
) -> dict[str, object]:
    return {
        "dispatch": {
            "mode": "external_agent_api",
            "frozenAgentSnapshot": frozen_agent_snapshot,
        },
        "evaluationId": evaluation_id,
        "maxSteps": max_steps,
        "parameters": {"retryEnabled": False},
    }


def display_name(risk_subtype: RiskSubtype) -> str:
    translations = risk_subtype.translations
    if isinstance(translations, dict):
        zh = translations.get("zh-CN")
        if isinstance(zh, dict) and isinstance(zh.get("name"), str):
            return zh["name"]
        en = translations.get("en-US")
        if isinstance(en, dict) and isinstance(en.get("name"), str):
            return en["name"]
    return risk_subtype.code


def store_skyvern_credential(args: argparse.Namespace) -> str | None:
    api_key = os.environ.get(str(args.skyvern_api_key_env), "").strip()
    if not api_key:
        return None
    return default_credential_store().store(
        {"type": "api_key_header", "headerName": "x-api-key", "secret": api_key}
    )


async def create_direct_run(
    args: argparse.Namespace, *, credential_ref: str | None
) -> tuple[int, int, int, int]:
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(BenchmarkSample, RiskSubtype)
                .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
                .where(BenchmarkSample.sample_id == args.sample_id)
                .limit(1)
            )
        ).one_or_none()
        if row is None:
            raise RuntimeError(f"sample not found: {args.sample_id}")

        sample, risk_subtype = row
        user = User(
            username=f"skyvern_eval_{suffix}_{uuid4().hex[:6]}",
            email=f"skyvern_eval_{suffix}_{uuid4().hex[:6]}@example.local",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        await db.flush()

        frozen_agent = build_skyvern_snapshot(args, credential_ref=credential_ref)
        run = TestRun(
            user_id=user.id,
            public_id=generate_public_id(),
            agent_name=str(frozen_agent["name"]),
            description="Direct one-sample Skyvern evaluator validation",
            submit_method="qa_skyvern_direct",
            public_to_leaderboard=False,
            leaderboard_display_mode="anonymous",
            request_id=f"qa_skyvern_{suffix}_{uuid4().hex[:8]}",
            agent_base_url=args.skyvern_base_url,
            credential_ref=None,
            status="paused",
            sample_query_snapshot={
                "mode": "direct_sample",
                "sampleId": sample.sample_id,
                "riskSubtype": risk_subtype.code,
            },
            execution_config=build_run_execution_config(
                frozen_agent_snapshot=frozen_agent,
                evaluation_id=None,
                max_steps=args.max_steps,
            ),
            total_samples=1,
            completed_samples=0,
            success_count=0,
            failed_count=0,
        )
        db.add(run)
        await db.flush()
        run.execution_config["evaluationId"] = run.public_id

        dataset = RunDataset(
            run_id=run.id,
            dataset_code=risk_subtype.code,
            dataset_name=display_name(risk_subtype),
            order_no=1,
            status="running",
            total_samples=1,
            completed_samples=0,
            started_at=datetime.now(timezone.utc),
        )
        db.add(dataset)
        await db.flush()

        run_sample = RunSample(
            run_id=run.id,
            sample_id_ref=sample.id,
            order_no=1,
            difficulty_version_code="qa_direct",
            difficulty_score_snapshot=sample.difficulty_score,
            completion_difficulty_snapshot=sample.difficulty_score,
            safety_difficulty_snapshot=sample.difficulty_score,
        )
        db.add(run_sample)
        await db.flush()

        execution = SampleExecution(
            run_id=run.id,
            run_sample_id=run_sample.id,
            sample_id_ref=sample.id,
            status="blocked",
            retry_no=0,
            attempt_reason="qa_direct",
        )
        db.add(execution)
        await db.commit()
        return run.id, dataset.id, execution.id, sample.id


async def snapshot_difficulty_stat(sample_db_id: int) -> dict[str, object] | None:
    async with AsyncSessionLocal() as db:
        row = await db.get(SampleDifficultyStat, sample_db_id)
        if row is None:
            return None
        return {
            column.name: getattr(row, column.name)
            for column in SampleDifficultyStat.__table__.columns
        }


async def restore_difficulty_stat(
    sample_db_id: int, snapshot: dict[str, object] | None
) -> None:
    async with AsyncSessionLocal() as db:
        row = await db.get(SampleDifficultyStat, sample_db_id)
        if snapshot is None:
            if row is not None:
                await db.delete(row)
            await db.commit()
            return
        if row is None:
            row = SampleDifficultyStat(**snapshot)
            db.add(row)
        else:
            for key, value in snapshot.items():
                setattr(row, key, value)
        await db.commit()


async def load_execution_target(execution_id: int) -> tuple[SampleJob, str]:
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(
                    SampleExecution,
                    BenchmarkSample,
                    TestRun.public_id,
                )
                .join(BenchmarkSample, SampleExecution.sample_id_ref == BenchmarkSample.id)
                .join(TestRun, SampleExecution.run_id == TestRun.id)
                .where(SampleExecution.id == execution_id)
            )
        ).one()
        execution, sample, public_id = row
        return (
            SampleJob(
                execution_id=execution.id,
                sample=SampleRuntimeTarget(
                    sample_db_id=sample.id,
                    sample_id=sample.sample_id,
                    sample_name=sample.sample_name or sample.sample_id,
                    resource_path=sample.resource_path,
                    entry_path=sample.entry_path,
                    user_goal=sample.user_goal,
                ),
            ),
            str(public_id),
        )


async def finalize_direct_run(run_id: int) -> None:
    async with AsyncSessionLocal() as db:
        run = await db.get(TestRun, run_id)
        if run is None:
            return
        statuses = list(
            (
                await db.execute(
                    select(SampleExecution.status).where(SampleExecution.run_id == run_id)
                )
            ).scalars()
        )
        final_status = "completed" if "done" in statuses else "failed"
        final_reason = (
            "qa_direct_completed" if final_status == "completed" else "qa_direct_failed"
        )
        await finalize_run(
            db,
            run,
            final_status=final_status,
            final_reason=final_reason,
            create_report=True,
        )


async def collect_summary(
    run_id: int, execution_id: int, *, sample_id: str
) -> dict[str, object]:
    async with AsyncSessionLocal() as db:
        run = await db.get(TestRun, run_id)
        execution = await db.get(SampleExecution, execution_id)
        summary = (
            await db.execute(
                select(ExecutionSummary).where(
                    ExecutionSummary.sample_execution_id == execution_id
                )
            )
        ).scalar_one_or_none()
        oracle_results = list(
            (
                await db.execute(
                    select(OracleResult).where(
                        OracleResult.sample_execution_id == execution_id
                    )
                )
            ).scalars()
        )
        artifacts = list(
            (
                await db.execute(
                    select(ExecutionArtifact.artifact_type).where(
                        ExecutionArtifact.sample_execution_id == execution_id
                    )
                )
            ).scalars()
        )
        return {
            "evaluationId": run.public_id if run else None,
            "runStatus": run.status if run else None,
            "sampleExecutionId": execution_id,
            "sampleExecutionStatus": execution.status if execution else None,
            "sampleId": sample_id,
            "entryUrl": execution.entry_url if execution else None,
            "workDir": execution.work_dir if execution else None,
            "finalLabel": summary.final_label if summary else None,
            "taskCompleted": summary.task_completed if summary else None,
            "harmDetected": summary.harm_detected if summary else None,
            "oracleResults": {
                "total": len(oracle_results),
                "matched": sum(1 for item in oracle_results if item.matched),
                "scores": [
                    None if item.score is None else float(item.score)
                    for item in oracle_results
                ],
            },
            "artifactTypes": sorted(set(artifacts)),
            "settings": {
                "WORKER_RUNNER_HOST": settings.WORKER_RUNNER_HOST,
                "WORKER_BROWSER_ENTRY_HOST": settings.WORKER_BROWSER_ENTRY_HOST,
                "WORKER_RUNTIME_LAUNCH_MODE": settings.WORKER_RUNTIME_LAUNCH_MODE,
                "LLM_JUDGE_PROVIDER": settings.LLM_JUDGE_PROVIDER,
                "LLM_JUDGE_MODEL": settings.LLM_JUDGE_MODEL,
                "LLM_JUDGE_BASE_URL": settings.LLM_JUDGE_BASE_URL,
                "LLM_DEFAULT_MODEL": settings.LLM_DEFAULT_MODEL,
                "LLM_BASE_URL": settings.LLM_BASE_URL,
            },
        }


async def amain(args: argparse.Namespace) -> int:
    credential_ref = store_skyvern_credential(args)
    try:
        run_id, dataset_id, execution_id, sample_db_id = await create_direct_run(
            args, credential_ref=credential_ref
        )
        difficulty_snapshot = await snapshot_difficulty_stat(sample_db_id)
        job, public_id = await load_execution_target(execution_id)
        dispatch_config = build_execution_config(
            frozen_agent_snapshot=build_skyvern_snapshot(
                args, credential_ref=credential_ref
            ),
            evaluation_id=public_id,
            max_steps=args.max_steps,
        )
        await execute_sample(
            run_id,
            dataset_id,
            job,
            dispatch_mode="external_agent_api",
            dispatch_config=dispatch_config,
            timeout_seconds=args.timeout_seconds,
        )
        await finalize_direct_run(run_id)
        await restore_difficulty_stat(sample_db_id, difficulty_snapshot)
        print(
            json.dumps(
                await collect_summary(run_id, execution_id, sample_id=args.sample_id),
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        if credential_ref:
            default_credential_store().delete(credential_ref)
    return 0


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(asyncio.run(amain(args)))
