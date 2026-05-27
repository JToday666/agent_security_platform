from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.benchmark import (
    AttackDeliveryType,
    BenchmarkSample,
    DatasetSource,
    RiskCategory,
    RiskSubtype,
)
from app.models.benchmark_run import (
    ExecutionArtifact,
    ExecutionSummary,
    RunDataset,
    RunReport,
    RunSample,
    SampleExecution,
    TestRun as RunModel,
)
from app.platform.db.session import AsyncSessionLocal, engine as async_engine
from app.worker.execution_persistence import (
    mark_execution_dispatching,
    mark_execution_system_error,
    persist_execution_artifacts_only,
)
from app.worker.sample_claims import claim_next_sample
from app.worker.sample_scheduler import (
    finalize_ready_runs_once,
    recover_stale_sample_claims_once,
    release_ready_samples_once,
)

pytestmark = pytest.mark.worker


@pytest_asyncio.fixture(autouse=True)
async def isolate_async_engine_pool_for_event_loop():
    await async_engine.dispose()
    yield
    await async_engine.dispose()


def _seed_sample_level_run(api_db_helper, *, terminal_first: bool = False) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    user_id, _ = api_db_helper.seed_user(
        username=f"{api_db_helper.prefix}_sample_sched_user",
        email=f"{api_db_helper.prefix}_sample_sched@example.com",
    )
    with api_db_helper.session() as session:
        category = RiskCategory(
            code=f"{api_db_helper.prefix}_sample_sched_category",
            name="sample scheduler category",
            meaning="sample scheduler tests",
            description="sample scheduler tests",
            sort_order=1,
            is_active=True,
        )
        source = DatasetSource(
            code=f"{api_db_helper.prefix}_sample_sched_source",
            name="sample scheduler source",
            is_active=True,
        )
        delivery = AttackDeliveryType(
            code=f"{api_db_helper.prefix}_sample_sched_delivery",
            name="sample scheduler delivery",
            is_active=True,
        )
        session.add_all([category, source, delivery])
        session.flush()

        subtypes: list[RiskSubtype] = []
        samples: list[BenchmarkSample] = []
        for index in range(2):
            subtype = RiskSubtype(
                category_id=category.id,
                code=f"{api_db_helper.prefix}_sample_sched_ds_{index}",
                name=f"sample scheduler dataset {index}",
                sort_order=index + 1,
                is_active=True,
            )
            session.add(subtype)
            session.flush()
            subtypes.append(subtype)

            sample = BenchmarkSample(
                dataset_source_id=source.id,
                sample_id=f"{api_db_helper.prefix}_sample_sched_sample_{index}",
                sample_name=f"sample scheduler sample {index}",
                resource_path=f"{api_db_helper.prefix}/sample_{index}",
                entry_path="index.html",
                user_goal="完成正常任务",
                attacker_goal="诱导攻击",
                attacker_is_user=False,
                attack_delivery_type_id=delivery.id,
                risk_subtype_id=subtype.id,
                risk_level=2,
                attack_level=2,
                difficulty_seed=Decimal("0.500"),
                difficulty_score=Decimal("0.500"),
                asset_type_id=None,
                expected_safe_behavior="拒绝攻击并完成正常任务",
                is_active=True,
            )
            session.add(sample)
            session.flush()
            samples.append(sample)

        run = RunModel(
            user_id=user_id,
            public_id=f"eval_{api_db_helper.prefix}_sample_sched",
            agent_name="sample scheduler agent",
            description=None,
            submit_method="api",
            public_to_leaderboard=False,
            request_id=f"{api_db_helper.prefix}_sample_sched_request",
            agent_base_url="https://example.com/agent",
            credential_ref=None,
            status="running",
            sample_query_snapshot={"datasetIds": [subtype.code for subtype in subtypes]},
            execution_config={
                "dispatchMode": "synthetic_local",
                "parameters": {"timeoutMinutes": 20},
            },
            total_samples=2,
            completed_samples=1 if terminal_first else 0,
            success_count=1 if terminal_first else 0,
            failed_count=0,
            created_at=now,
            updated_at=now,
            started_at=now,
        )
        session.add(run)
        session.flush()

        datasets: list[RunDataset] = []
        for index, subtype in enumerate(subtypes):
            dataset = RunDataset(
                run_id=run.id,
                dataset_code=subtype.code,
                dataset_name=subtype.name,
                order_no=index + 1,
                status="completed" if terminal_first and index == 0 else "pending",
                total_samples=1,
                completed_samples=1 if terminal_first and index == 0 else 0,
                started_at=now if index == 0 else None,
                finished_at=now if terminal_first and index == 0 else None,
            )
            session.add(dataset)
            session.flush()
            datasets.append(dataset)

        executions: list[SampleExecution] = []
        for index, sample in enumerate(samples):
            run_sample = RunSample(
                run_id=run.id,
                sample_id_ref=sample.id,
                order_no=index + 1,
                difficulty_version_code="legacy_current",
                difficulty_score_snapshot=Decimal("0.500"),
                completion_difficulty_snapshot=Decimal("0.500"),
                safety_difficulty_snapshot=Decimal("0.500"),
            )
            session.add(run_sample)
            session.flush()
            execution = SampleExecution(
                run_id=run.id,
                run_sample_id=run_sample.id,
                sample_id_ref=sample.id,
                status="done" if terminal_first and index == 0 else "blocked",
                retry_no=0,
                finished_at=now if terminal_first and index == 0 else None,
            )
            session.add(execution)
            session.flush()
            executions.append(execution)
            if terminal_first and index == 0:
                session.add(
                    ExecutionSummary(
                        sample_execution_id=execution.id,
                        task_completed=True,
                        harm_detected=False,
                        summary_text="ok",
                        final_label="safe",
                    )
                )

        session.commit()
        return {
            "run_id": run.id,
            "first_dataset_id": datasets[0].id,
            "second_dataset_id": datasets[1].id,
            "first_execution_id": executions[0].id,
            "second_execution_id": executions[1].id,
        }


@pytest.mark.asyncio
async def test_scheduler_releases_only_current_dataset_and_respects_run_quota(
    api_db_helper, monkeypatch
) -> None:
    ids = _seed_sample_level_run(api_db_helper)

    from app.worker import sample_scheduler

    monkeypatch.setattr(sample_scheduler.settings, "SCHEDULER_RELEASE_BATCH_SIZE", 50)
    monkeypatch.setattr(sample_scheduler.settings, "GLOBAL_MAX_IN_FLIGHT_SAMPLES", 16)
    monkeypatch.setattr(sample_scheduler.settings, "RUN_MAX_IN_FLIGHT_SAMPLES", 1)
    monkeypatch.setattr(sample_scheduler.settings, "USER_MAX_IN_FLIGHT_SAMPLES", 8)
    monkeypatch.setattr(sample_scheduler.settings, "AGENT_MAX_IN_FLIGHT_SAMPLES", 4)

    async with AsyncSessionLocal() as db:
        released = await release_ready_samples_once(db)

    with api_db_helper.session() as session:
        run = session.get(RunModel, ids["run_id"])
        first_dataset = session.get(RunDataset, ids["first_dataset_id"])
        second_dataset = session.get(RunDataset, ids["second_dataset_id"])
        first_execution = session.get(SampleExecution, ids["first_execution_id"])
        second_execution = session.get(SampleExecution, ids["second_execution_id"])

    assert released == 1
    assert run.status == "running"
    assert first_dataset.status == "running"
    assert second_dataset.status == "pending"
    assert first_execution.status == "ready"
    assert first_execution.ready_at is not None
    assert second_execution.status == "blocked"


@pytest.mark.asyncio
async def test_scheduler_advances_to_next_dataset_after_current_dataset_terminal(
    api_db_helper, monkeypatch
) -> None:
    ids = _seed_sample_level_run(api_db_helper, terminal_first=True)

    from app.worker import sample_scheduler

    monkeypatch.setattr(sample_scheduler.settings, "RUN_MAX_IN_FLIGHT_SAMPLES", 4)

    async with AsyncSessionLocal() as db:
        released = await release_ready_samples_once(db)

    with api_db_helper.session() as session:
        second_dataset = session.get(RunDataset, ids["second_dataset_id"])
        second_execution = session.get(SampleExecution, ids["second_execution_id"])

    assert released == 1
    assert second_dataset.status == "running"
    assert second_execution.status == "ready"


@pytest.mark.asyncio
async def test_sample_worker_claim_writes_sample_level_lease(
    api_db_helper, monkeypatch
) -> None:
    ids = _seed_sample_level_run(api_db_helper)

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, ids["first_execution_id"])
        assert execution is not None
        execution.status = "ready"
        await db.commit()

    from app.worker import sample_claims

    monkeypatch.setattr(sample_claims.settings, "SAMPLE_CLAIM_STALE_AFTER_SECONDS", 90)

    async with AsyncSessionLocal() as db:
        claimed = await claim_next_sample(db, "sample-worker-test")

    assert claimed is not None
    assert claimed.id == ids["first_execution_id"]
    assert claimed.status == "claimed"
    assert claimed.claimed_by == "sample-worker-test"
    assert claimed.claimed_at is not None
    assert claimed.claim_heartbeat_at is not None
    assert claimed.lease_expires_at is not None
    assert claimed.claim_token is not None


@pytest.mark.asyncio
async def test_scheduler_recovers_stale_claimed_sample(api_db_helper) -> None:
    ids = _seed_sample_level_run(api_db_helper)
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=10)

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, ids["first_execution_id"])
        assert execution is not None
        execution.status = "claimed"
        execution.claimed_by = "dead-worker"
        execution.claimed_at = stale_time
        execution.claim_heartbeat_at = stale_time
        execution.lease_expires_at = stale_time
        execution.claim_token = "old-token"
        await db.commit()

    async with AsyncSessionLocal() as db:
        recovered = await recover_stale_sample_claims_once(db)

    with api_db_helper.session() as session:
        execution = session.get(SampleExecution, ids["first_execution_id"])

    assert recovered == 1
    assert execution.status == "ready"
    assert execution.claimed_by is None
    assert execution.claim_token is None
    assert execution.attempt_reason == "lease_recovered"


@pytest.mark.asyncio
async def test_stale_claim_token_cannot_update_reclaimed_sample(api_db_helper) -> None:
    ids = _seed_sample_level_run(api_db_helper)

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, ids["first_execution_id"])
        assert execution is not None
        execution.status = "claimed"
        execution.claimed_by = "new-worker"
        execution.claim_token = "new-token"
        await db.commit()

    updated = await mark_execution_dispatching(
        ids["first_execution_id"], claim_token="old-token"
    )

    with api_db_helper.session() as session:
        execution = session.get(SampleExecution, ids["first_execution_id"])

    assert updated is False
    assert execution.status == "claimed"
    assert execution.claim_token == "new-token"


@pytest.mark.asyncio
async def test_finalizer_generates_report_after_all_samples_reach_terminal_state(
    api_db_helper,
) -> None:
    ids = _seed_sample_level_run(api_db_helper, terminal_first=True)
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, ids["second_execution_id"])
        assert execution is not None
        execution.status = "done"
        execution.finished_at = now
        db.add(
            ExecutionSummary(
                sample_execution_id=execution.id,
                task_completed=True,
                harm_detected=False,
                summary_text="ok",
                final_label="safe",
            )
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        finalized = await finalize_ready_runs_once(db)

    with api_db_helper.session() as session:
        run = session.get(RunModel, ids["run_id"])
        reports = list(
            session.execute(
                select(RunReport).where(RunReport.run_id == ids["run_id"])
            ).scalars()
        )

    assert finalized == 1
    assert run.status == "completed"
    assert run.completed_samples == 2
    assert reports
    assert reports[0].report_status == "available"


@pytest.mark.asyncio
async def test_system_error_creates_retry_attempt_without_counting_sample_complete(
    api_db_helper, monkeypatch
) -> None:
    ids = _seed_sample_level_run(api_db_helper)

    from app.worker import execution_persistence

    monkeypatch.setattr(execution_persistence.settings, "SAMPLE_MAX_ATTEMPTS", 2)

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, ids["first_execution_id"])
        assert execution is not None
        execution.status = "executing"
        await db.commit()

    await mark_execution_system_error(
        ids["first_execution_id"],
        ids["run_id"],
        ids["first_dataset_id"],
        RuntimeError("runtime crashed"),
    )

    with api_db_helper.session() as session:
        attempts = list(
            session.execute(
                select(SampleExecution)
                .where(SampleExecution.run_id == ids["run_id"])
                .order_by(SampleExecution.run_sample_id.asc(), SampleExecution.retry_no.asc())
            ).scalars()
        )
        first_attempts = [
            attempt
            for attempt in attempts
            if attempt.run_sample_id == attempts[0].run_sample_id
        ]
        run = session.get(RunModel, ids["run_id"])
        dataset = session.get(RunDataset, ids["first_dataset_id"])

    assert [attempt.retry_no for attempt in first_attempts] == [0, 1]
    assert first_attempts[0].status == "error"
    assert first_attempts[1].status == "ready"
    assert first_attempts[1].attempt_reason == "system_error_retry"
    assert first_attempts[1].ready_at is not None
    assert run.completed_samples == 0
    assert dataset.completed_samples == 0


@pytest.mark.asyncio
async def test_system_error_respects_disabled_retry_setting(
    api_db_helper, monkeypatch
) -> None:
    ids = _seed_sample_level_run(api_db_helper)

    from app.worker import execution_persistence

    monkeypatch.setattr(execution_persistence.settings, "SAMPLE_MAX_ATTEMPTS", 2)

    async with AsyncSessionLocal() as db:
        run = await db.get(RunModel, ids["run_id"])
        assert run is not None
        run.execution_config = {
            "dispatchMode": "external_agent",
            "parameters": {"timeoutMinutes": 25, "retryEnabled": False},
        }
        execution = await db.get(SampleExecution, ids["first_execution_id"])
        assert execution is not None
        execution.status = "executing"
        await db.commit()

    await mark_execution_system_error(
        ids["first_execution_id"],
        ids["run_id"],
        ids["first_dataset_id"],
        RuntimeError("runtime crashed"),
    )

    with api_db_helper.session() as session:
        original = session.get(SampleExecution, ids["first_execution_id"])
        assert original is not None
        attempts = list(
            session.execute(
                select(SampleExecution)
                .where(SampleExecution.run_sample_id == original.run_sample_id)
                .order_by(SampleExecution.retry_no.asc())
            ).scalars()
        )
        run = session.get(RunModel, ids["run_id"])
        dataset = session.get(RunDataset, ids["first_dataset_id"])

    assert len(attempts) == 1
    assert attempts[0].status == "error"
    assert attempts[0].retry_no == 0
    assert run.completed_samples == 1
    assert run.failed_count == 1
    assert dataset.completed_samples == 1


@pytest.mark.asyncio
async def test_failed_execution_can_persist_available_evidence_artifacts(
    api_db_helper, tmp_path
) -> None:
    ids = _seed_sample_level_run(api_db_helper)
    work_dir = tmp_path / "workdir"
    run_dir = work_dir / "agent_runtime" / "runs" / "exec-1"
    run_dir.mkdir(parents=True)
    (run_dir / "external_agent_invocation.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "agentId": "agt_failed",
                "outcome": {"status": "failed", "errorClass": "http_error"},
                "httpCalls": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    prepared = SimpleNamespace(
        work_dir=work_dir,
        run_dir=run_dir,
        stdout_log=work_dir / "stdout.log",
        stderr_log=work_dir / "stderr.log",
        execution_id=ids["first_execution_id"],
    )

    async with AsyncSessionLocal() as db:
        execution = await db.get(SampleExecution, ids["first_execution_id"])
        assert execution is not None
        execution.status = "executing"
        await db.commit()

    await persist_execution_artifacts_only(
        ids["first_execution_id"],
        prepared=prepared,
    )

    with api_db_helper.session() as session:
        artifact = session.execute(
            select(ExecutionArtifact).where(
                ExecutionArtifact.sample_execution_id == ids["first_execution_id"],
                ExecutionArtifact.artifact_type == "external_agent_invocation",
            )
        ).scalar_one()

    assert artifact.storage_uri.endswith(
        "/agent_runtime/runs/exec-1/external_agent_invocation.json"
    )
    assert artifact.artifact_metadata["relativePath"] == (
        "agent_runtime/runs/exec-1/external_agent_invocation.json"
    )


@pytest.mark.asyncio
async def test_finalizer_counts_retried_sample_once(api_db_helper) -> None:
    ids = _seed_sample_level_run(api_db_helper, terminal_first=True)
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        original = await db.get(SampleExecution, ids["second_execution_id"])
        assert original is not None
        original.status = "error"
        original.finished_at = now
        original.error_message = "RuntimeError: crashed"
        retry = SampleExecution(
            run_id=original.run_id,
            run_sample_id=original.run_sample_id,
            sample_id_ref=original.sample_id_ref,
            status="done",
            retry_no=1,
            finished_at=now,
            attempt_reason="system_error_retry",
        )
        db.add(retry)
        await db.flush()
        db.add(
            ExecutionSummary(
                sample_execution_id=retry.id,
                task_completed=True,
                harm_detected=False,
                summary_text="retry ok",
                final_label="safe",
            )
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        finalized = await finalize_ready_runs_once(db)

    with api_db_helper.session() as session:
        run = session.get(RunModel, ids["run_id"])
        first_dataset = session.get(RunDataset, ids["first_dataset_id"])
        second_dataset = session.get(RunDataset, ids["second_dataset_id"])

    assert finalized == 1
    assert run.status == "completed"
    assert run.completed_samples == 2
    assert run.success_count == 2
    assert run.failed_count == 0
    assert first_dataset.completed_samples == 1
    assert second_dataset.completed_samples == 1
