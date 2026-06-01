from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import (
    ExecutionArtifact,
    ExecutionSummary,
    OracleResult,
    RunDataset,
    RunSample,
    SampleExecution,
    TestRun as RunModel,
)
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal, engine as async_engine
from app.worker.execution_persistence import persist_raw_runtime_result

pytestmark = pytest.mark.worker


@pytest.fixture(autouse=True)
async def isolate_async_engine_pool_for_event_loop():
    await async_engine.dispose()
    yield
    await async_engine.dispose()


def _write_raw_runtime_files(work_dir: Path) -> SimpleNamespace:
    run_dir = work_dir / "agent_runtime" / "runs" / "rt_gold"
    run_dir.mkdir(parents=True)
    (run_dir / "dispatch_context.json").write_text(
        json.dumps({"mode": "external_agent_api"}), encoding="utf-8"
    )
    (run_dir / "external_agent_invocation.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "sampleId": "gold_sample",
                "outcome": {"status": "completed"},
                "httpCalls": [],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "finalize.json").write_text(
        json.dumps({"done": True, "done_reason": "external_agent_completed"}),
        encoding="utf-8",
    )
    (run_dir / "meta.json").write_text(
        json.dumps({"run_id": "rt_gold"}), encoding="utf-8"
    )
    (run_dir / "runtime_context.json").write_text(
        json.dumps({"sampleExecutionId": 0}), encoding="utf-8"
    )
    stdout_log = run_dir / "runner_stdout.log"
    stderr_log = run_dir / "runner_stderr.log"
    stdout_log.write_text("stdout\n", encoding="utf-8")
    stderr_log.write_text("", encoding="utf-8")
    return SimpleNamespace(
        work_dir=work_dir,
        run_dir=run_dir,
        project_root=work_dir,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        execution_id=0,
    )


def _seed_execution(api_db_helper) -> tuple[int, int, int]:
    dataset_code = api_db_helper.seed_dataset()
    user_id, _token = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_gold_user",
        email=f"{api_db_helper.prefix}_gold@example.com",
    )
    evaluation_id = api_db_helper.seed_evaluation_run(
        user_id=user_id,
        dataset_code=dataset_code,
        status="running",
    )
    with api_db_helper.session() as session:
        run = session.execute(
            select(RunModel).where(RunModel.public_id == evaluation_id)
        ).scalar_one()
        dataset = session.execute(
            select(RunDataset).where(RunDataset.run_id == run.id)
        ).scalar_one()
        sample = session.execute(
            select(BenchmarkSample)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(RiskSubtype.code == dataset_code)
        ).scalar_one()
        run_sample = RunSample(
            run_id=run.id,
            sample_id_ref=sample.id,
            order_no=1,
            difficulty_version_code="gold_set_test",
            difficulty_score_snapshot=sample.difficulty_score,
            completion_difficulty_snapshot=sample.difficulty_score,
            safety_difficulty_snapshot=sample.difficulty_score,
        )
        session.add(run_sample)
        session.flush()
        execution = SampleExecution(
            run_id=run.id,
            run_sample_id=run_sample.id,
            sample_id_ref=sample.id,
            status="verifying",
            retry_no=0,
            attempt_reason="gold_set_test",
        )
        session.add(execution)
        session.commit()
        return run.id, dataset.id, execution.id


@pytest.mark.db
@pytest.mark.asyncio
async def test_raw_runtime_persistence_archives_artifacts_without_evaluator_outputs(
    selectable_api_db_helper, tmp_path: Path, monkeypatch
) -> None:
    run_id, dataset_id, execution_id = _seed_execution(selectable_api_db_helper)
    prepared = _write_raw_runtime_files(tmp_path / "workdir")
    prepared.execution_id = execution_id
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr(settings, "ARTIFACT_ROOT_DIR", str(artifact_root))

    await persist_raw_runtime_result(
        execution_id,
        run_id,
        dataset_id,
        prepared=prepared,
        success=True,
        final_status="done",
    )

    async with AsyncSessionLocal() as db:
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
        oracle_count = len(
            (
                await db.execute(
                    select(OracleResult).where(
                        OracleResult.sample_execution_id == execution_id
                    )
                )
            ).scalars().all()
        )
        summary_count = len(
            (
                await db.execute(
                    select(ExecutionSummary).where(
                        ExecutionSummary.sample_execution_id == execution_id
                    )
                )
            ).scalars().all()
        )

    artifact_types = {artifact.artifact_type for artifact in artifacts}
    assert execution is not None
    assert execution.status == "done"
    assert "external_agent_invocation" in artifact_types
    assert "finalize_payload" in artifact_types
    assert "event_log" in artifact_types
    assert "artifact_manifest" in artifact_types
    assert "analysis_result" not in artifact_types
    assert not (prepared.run_dir / "analysis_result.json").exists()
    assert oracle_count == 0
    assert summary_count == 0
