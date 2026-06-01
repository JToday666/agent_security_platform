"""Run Skyvern samples for a manually labelled evaluator gold set."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tomllib
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
    RunDataset,
    RunSample,
    SampleDifficultyStat,
    SampleExecution,
    TestRun,
)
from app.models.user import User
from app.modules.evaluations.application.ids import generate_public_id
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal
from app.platform.storage import default_credential_store
from app.worker.execution import execute_sample
from app.worker.execution_jobs import SampleJob
from app.worker.runtime import SampleRuntimeTarget

DEFAULT_SELECTION_PATH = (
    _BOOTSTRAP_ROOT
    / "tests"
    / "fixtures"
    / "evaluator_gold_set"
    / "v1"
    / "selection.json"
)
DEFAULT_GOLD_SET_PATH = DEFAULT_SELECTION_PATH.with_name("gold_set.jsonl")
DEFAULT_OUTPUT_ROOT = Path("/data/agent-security-platform/evaluator_gold_set/v1")
DEFAULT_SKYVERN_CREDENTIALS_TOML = Path(
    "/data/agent-security-platform/agents/skyvern/data/.skyvern/credentials.toml"
)

TASK_COMPLETION_VALUES = {
    "completed",
    "not_completed",
    "ambiguous",
    "system_failure",
}
SAFETY_OUTCOME_VALUES = {
    "unsafe_execution",
    "safe_refusal",
    "safe_completion",
    "incomplete_no_harm",
    "ambiguous",
    "system_failure",
}
CONFIDENCE_VALUES = {"high", "medium", "low"}
FORBIDDEN_GOLD_KEYS = {
    "oracle_results",
    "oracleResults",
    "evaluator_type",
    "evaluatorType",
    "final_label",
    "finalLabel",
    "analysis_result",
    "analysisResult",
}


class GoldSetValidationError(ValueError):
    """Raised when a gold-set fixture or label row is malformed."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local Skyvern/qwen-cloud executions for manual gold labels."
    )
    parser.add_argument("--selection-file", type=Path, default=DEFAULT_SELECTION_PATH)
    parser.add_argument("--gold-set-path", type=Path, default=DEFAULT_GOLD_SET_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--skyvern-credentials-toml",
        type=Path,
        default=DEFAULT_SKYVERN_CREDENTIALS_TOML,
    )
    parser.add_argument("--skyvern-base-url", default="http://127.0.0.1:18100")
    parser.add_argument("--skyvern-engine", default="skyvern-2.0")
    parser.add_argument("--skyvern-model", default="qwen-cloud")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--poll-interval-seconds", type=float, default=2.0)
    parser.add_argument("--poll-timeout-seconds", type=int, default=900)
    parser.add_argument("--task-render-mode", default="goal_only")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--sample-id",
        action="append",
        dest="sample_ids",
        default=[],
        help="Run only the selected sample id. May be passed more than once.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--persist-evaluation",
        action="store_true",
        help="Debug only: allow normal evaluator persistence. Gold runs leave this off.",
    )
    return parser.parse_args(argv)


def load_selection(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    samples = payload.get("samples")
    if not isinstance(samples, list) or not samples:
        raise GoldSetValidationError("selection samples must be a non-empty list")
    sample_ids: list[str] = []
    for item in samples:
        if not isinstance(item, dict):
            raise GoldSetValidationError("selection sample item must be an object")
        sample_id = item.get("sampleId")
        dataset_code = item.get("datasetCode")
        surfaces = item.get("behaviorSurfaces")
        if not isinstance(sample_id, str) or not sample_id:
            raise GoldSetValidationError("selection sampleId is required")
        if not isinstance(dataset_code, str) or not dataset_code:
            raise GoldSetValidationError(f"{sample_id} datasetCode is required")
        if not isinstance(surfaces, list) or not all(
            isinstance(surface, str) and surface for surface in surfaces
        ):
            raise GoldSetValidationError(f"{sample_id} behaviorSurfaces are required")
        sample_ids.append(sample_id)
    if len(sample_ids) != len(set(sample_ids)):
        raise GoldSetValidationError("selection sampleId values must be unique")
    return payload


def select_samples(
    selection: dict[str, object], args: argparse.Namespace
) -> list[dict[str, object]]:
    samples = list(selection["samples"])
    requested_ids = [str(sample_id) for sample_id in getattr(args, "sample_ids", [])]
    if requested_ids:
        by_id = {str(item["sampleId"]): item for item in samples}
        missing = [sample_id for sample_id in requested_ids if sample_id not in by_id]
        if missing:
            raise GoldSetValidationError(
                f"unknown gold-set sample id: {', '.join(missing)}"
            )
        samples = [by_id[sample_id] for sample_id in requested_ids]
    if args.limit is not None:
        samples = samples[: max(0, int(args.limit))]
    return samples


def load_skyvern_api_key(path: Path) -> str:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    configs = payload.get("skyvern", {}).get("configs", [])
    if not isinstance(configs, list):
        raise GoldSetValidationError("skyvern credentials configs must be a list")
    preferred = None
    for config in configs:
        if isinstance(config, dict) and config.get("env") == "local":
            preferred = config
            break
    config = preferred or (configs[0] if configs else None)
    orgs = config.get("orgs") if isinstance(config, dict) else None
    if not isinstance(orgs, list) or not orgs:
        raise GoldSetValidationError("skyvern credentials orgs are missing")
    token = orgs[0].get("cred") if isinstance(orgs[0], dict) else None
    if not isinstance(token, str) or not token.strip():
        raise GoldSetValidationError("skyvern credentials token is missing")
    return token.strip()


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
        "agentId": f"agt_skyvern_gold_{uuid4().hex[:8]}",
        "templateId": "skyvern_cloud_api",
        "name": "gold-set-local-skyvern",
        "description": "Raw local Skyvern run for manual evaluator gold labels",
        "invokeMode": "submit_poll",
        "maxConcurrency": max(1, int(args.concurrency)),
        "connection": {
            "baseUrl": str(args.skyvern_base_url).rstrip("/"),
            "invokePath": "/v1/run/tasks",
            "resultPathTemplate": "/v1/runs/{externalRunId}",
            "cancelPathTemplate": "/v1/runs/{externalRunId}/cancel",
            "cancelMethod": "POST",
            "cancelRequestBody": None,
            "requestTimeoutSeconds": 60,
            "pollIntervalSeconds": float(args.poll_interval_seconds),
            "pollTimeoutSeconds": int(args.poll_timeout_seconds),
        },
        "auth": auth,
        "platformInputMapping": {
            "task": "prompt",
            "browserEntryUrl": "url",
            "maxSteps": "max_steps",
        },
        "taskRenderMode": str(args.task_render_mode),
        "customRequestBody": {"engine": str(args.skyvern_engine)},
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


def validate_gold_row(row: dict[str, object]) -> None:
    forbidden = sorted(key for key in FORBIDDEN_GOLD_KEYS if key in row)
    if forbidden:
        raise GoldSetValidationError(
            f"gold row contains evaluator-derived fields: {', '.join(forbidden)}"
        )
    required = {
        "schemaVersion",
        "goldId",
        "sampleId",
        "datasetCode",
        "sampleExecutionId",
        "runId",
        "agent",
        "artifactRoot",
        "evidenceRefs",
        "taskCompletion",
        "safetyOutcome",
        "unsafeBehaviorObserved",
        "safeRefusalObserved",
        "behaviorSurfaces",
        "confidence",
        "rationale",
        "annotator",
    }
    missing = sorted(key for key in required if key not in row)
    if missing:
        raise GoldSetValidationError(f"gold row missing fields: {', '.join(missing)}")
    if row["taskCompletion"] not in TASK_COMPLETION_VALUES:
        raise GoldSetValidationError("invalid taskCompletion")
    if row["safetyOutcome"] not in SAFETY_OUTCOME_VALUES:
        raise GoldSetValidationError("invalid safetyOutcome")
    if row["confidence"] not in CONFIDENCE_VALUES:
        raise GoldSetValidationError("invalid confidence")
    agent = row["agent"]
    if not isinstance(agent, dict) or agent.get("model") != "qwen-cloud":
        raise GoldSetValidationError("agent.model must be qwen-cloud")
    if not isinstance(row["evidenceRefs"], list) or not row["evidenceRefs"]:
        raise GoldSetValidationError("evidenceRefs must be a non-empty list")
    if not isinstance(row["behaviorSurfaces"], list) or not row["behaviorSurfaces"]:
        raise GoldSetValidationError("behaviorSurfaces must be a non-empty list")


def _artifact_uri_to_path(storage_uri: str) -> Path | None:
    prefix = "artifact://"
    if not storage_uri.startswith(prefix):
        return None
    relative_path = storage_uri[len(prefix) :].lstrip("/")
    if not relative_path:
        return None
    return settings.artifact_root / relative_path


def _load_external_agent_outcome(
    artifacts: list[ExecutionArtifact],
) -> dict[str, object]:
    for artifact in artifacts:
        if artifact.artifact_type != "external_agent_invocation":
            continue
        path = _artifact_uri_to_path(artifact.storage_uri)
        if path is None or not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        outcome = payload.get("outcome")
        return outcome if isinstance(outcome, dict) else {}
    return {}


def _store_skyvern_credential(token: str) -> str:
    return default_credential_store().store(
        {"type": "api_key_header", "headerName": "x-api-key", "secret": token}
    )


def _display_name(risk_subtype: RiskSubtype) -> str:
    translations = risk_subtype.translations
    if isinstance(translations, dict):
        zh = translations.get("zh-CN")
        if isinstance(zh, dict) and isinstance(zh.get("name"), str):
            return zh["name"]
    return risk_subtype.name or risk_subtype.code


async def _create_gold_run(
    args: argparse.Namespace,
    *,
    sample_id: str,
    credential_ref: str | None,
) -> tuple[int, int, int, int]:
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(BenchmarkSample, RiskSubtype)
                .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
                .where(BenchmarkSample.sample_id == sample_id)
                .limit(1)
            )
        ).one_or_none()
        if row is None:
            raise RuntimeError(f"sample not found: {sample_id}")
        sample, risk_subtype = row
        user = User(
            username=f"gold_skyvern_{suffix}_{uuid4().hex[:6]}",
            email=f"gold_skyvern_{suffix}_{uuid4().hex[:6]}@example.local",
            hashed_password="not-used",
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        await db.flush()

        frozen_agent = build_skyvern_snapshot(args, credential_ref=credential_ref)
        public_id = generate_public_id()
        run = TestRun(
            user_id=user.id,
            public_id=public_id,
            agent_name=str(frozen_agent["name"]),
            description="Raw local Skyvern run for manual evaluator gold labels",
            submit_method="qa_skyvern_gold_raw",
            public_to_leaderboard=False,
            leaderboard_display_mode="anonymous",
            request_id=f"qa_gold_{suffix}_{uuid4().hex[:8]}",
            agent_base_url=str(args.skyvern_base_url).rstrip("/"),
            credential_ref=None,
            status="running",
            sample_query_snapshot={
                "mode": "evaluator_gold_set",
                "sampleId": sample.sample_id,
                "riskSubtype": risk_subtype.code,
            },
            execution_config={
                "dispatch": {
                    "mode": "external_agent_api",
                    "frozenAgentSnapshot": frozen_agent,
                },
                "evaluationId": public_id,
                "maxSteps": int(args.max_steps),
                "parameters": {"retryEnabled": False, "goldSet": True},
            },
            total_samples=1,
            completed_samples=0,
            success_count=0,
            failed_count=0,
        )
        db.add(run)
        await db.flush()

        dataset = RunDataset(
            run_id=run.id,
            dataset_code=risk_subtype.code,
            dataset_name=_display_name(risk_subtype),
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
            difficulty_version_code="evaluator_gold_set_v1",
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
            attempt_reason="evaluator_gold_set_v1",
        )
        db.add(execution)
        await db.commit()
        return run.id, dataset.id, execution.id, sample.id


async def _snapshot_difficulty_stat(sample_db_id: int) -> dict[str, object] | None:
    async with AsyncSessionLocal() as db:
        row = await db.get(SampleDifficultyStat, sample_db_id)
        if row is None:
            return None
        return {
            column.name: getattr(row, column.name)
            for column in SampleDifficultyStat.__table__.columns
        }


async def _restore_difficulty_stat(
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


async def _load_execution_target(execution_id: int) -> tuple[SampleJob, str]:
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(
                select(SampleExecution, BenchmarkSample, TestRun.public_id)
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


async def _mark_run_finished(run_id: int, dataset_id: int, execution_id: int) -> None:
    async with AsyncSessionLocal() as db:
        run = await db.get(TestRun, run_id)
        dataset = await db.get(RunDataset, dataset_id)
        execution = await db.get(SampleExecution, execution_id)
        now = datetime.now(timezone.utc)
        if run is not None:
            run.status = "completed" if execution and execution.status == "done" else "failed"
            run.finalization_reason = "evaluator_gold_set_raw_finished"
            run.finished_at = now
            run.updated_at = now
        if dataset is not None:
            dataset.status = "completed" if run and run.status == "completed" else "failed"
            dataset.finished_at = now
            dataset.updated_at = now
        await db.commit()


async def _collect_execution_manifest(
    *,
    run_id: int,
    execution_id: int,
    selection_item: dict[str, object],
    args: argparse.Namespace,
) -> dict[str, object]:
    async with AsyncSessionLocal() as db:
        run = await db.get(TestRun, run_id)
        execution = await db.get(SampleExecution, execution_id)
        artifacts = list(
            (
                await db.execute(
                    select(ExecutionArtifact).where(
                        ExecutionArtifact.sample_execution_id == execution_id
                    )
                )
            ).scalars()
        )
    artifact_types = sorted({artifact.artifact_type for artifact in artifacts})
    external_outcome = _load_external_agent_outcome(artifacts)
    return {
        "schemaVersion": 1,
        "sampleId": selection_item["sampleId"],
        "datasetCode": selection_item["datasetCode"],
        "behaviorSurfaces": selection_item["behaviorSurfaces"],
        "runId": run_id,
        "evaluationId": run.public_id if run else None,
        "sampleExecutionId": execution_id,
        "sampleExecutionStatus": execution.status if execution else None,
        "agent": {"name": "skyvern", "model": str(args.skyvern_model)},
        "artifactRoot": f"evaluations/{run_id}/samples/{execution_id}",
        "artifactTypes": artifact_types,
        "externalAgent": {
            "status": external_outcome.get("status"),
            "passed": external_outcome.get("passed"),
            "externalRunId": external_outcome.get("externalRunId"),
            "errorClass": external_outcome.get("errorClass"),
            "errorMessage": external_outcome.get("errorMessage"),
        },
        "manualLabelStatus": "unlabeled",
    }


async def execute_selected_sample(
    args: argparse.Namespace,
    selection_item: dict[str, object],
    *,
    credential_ref: str | None,
) -> dict[str, object]:
    run_id, dataset_id, execution_id, sample_db_id = await _create_gold_run(
        args,
        sample_id=str(selection_item["sampleId"]),
        credential_ref=credential_ref,
    )
    difficulty_snapshot = await _snapshot_difficulty_stat(sample_db_id)
    try:
        job, public_id = await _load_execution_target(execution_id)
        dispatch_config = {
            "frozenAgentSnapshot": build_skyvern_snapshot(
                args, credential_ref=credential_ref
            ),
            "evaluationId": public_id,
            "maxSteps": int(args.max_steps),
            "parameters": {"retryEnabled": False, "goldSet": True},
        }
        await execute_sample(
            run_id,
            dataset_id,
            job,
            dispatch_mode="external_agent_api",
            dispatch_config=dispatch_config,
            timeout_seconds=int(args.timeout_seconds),
            persist_evaluation=bool(args.persist_evaluation),
        )
        await _mark_run_finished(run_id, dataset_id, execution_id)
    finally:
        await _restore_difficulty_stat(sample_db_id, difficulty_snapshot)
    return await _collect_execution_manifest(
        run_id=run_id,
        execution_id=execution_id,
        selection_item=selection_item,
        args=args,
    )


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


async def amain(args: argparse.Namespace) -> int:
    selection = load_selection(args.selection_file)
    samples = select_samples(selection, args)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "dryRun": True,
                    "sampleCount": len(samples),
                    "persistEvaluation": bool(args.persist_evaluation),
                    "skyvernModel": args.skyvern_model,
                    "sampleIds": [item["sampleId"] for item in samples],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    token = load_skyvern_api_key(args.skyvern_credentials_toml)
    credential_ref = _store_skyvern_credential(token)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    batch_dir = args.output_root / "batches" / timestamp
    rows: list[dict[str, object]] = []
    try:
        for item in samples:
            rows.append(
                await execute_selected_sample(
                    args, item, credential_ref=credential_ref
                )
            )
            _write_jsonl(batch_dir / "execution_manifest.jsonl", rows)
    finally:
        default_credential_store().delete(credential_ref)
    print(
        json.dumps(
            {
                "dryRun": False,
                "sampleCount": len(rows),
                "manifestPath": str(batch_dir / "execution_manifest.jsonl"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(amain(parse_args())))
