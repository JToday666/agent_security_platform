from __future__ import annotations

import sys
from argparse import Namespace
from io import StringIO
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import (
    RunSample,
    RuntimeSession,
    SampleDifficultyStat,
    SampleExecution,
    TestRun as RunModel,
)
from app.modules.runtime_gateway.session_store import hash_runtime_token
from tests.helpers.api_db import ApiDbHelper
from tests.helpers.scripts import load_module_from_path


@pytest.fixture(scope="module")
def e2e_module(backend_root: Path):
    return load_module_from_path(
        "e2e_local_run_under_test", backend_root / "scripts" / "qa" / "e2e_local_run.py"
    )


@pytest.fixture(scope="module")
def skyvern_direct_module(backend_root: Path):
    return load_module_from_path(
        "run_skyvern_sample_once_under_test",
        backend_root / "scripts" / "qa" / "run_skyvern_sample_once.py",
    )


def test_no_dataset_import_mode_fails_without_running_imports(e2e_module, monkeypatch) -> None:
    monkeypatch.setattr(e2e_module, "count_active_samples", lambda _dataset_code: 0)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("dataset import command must not run")

    monkeypatch.setattr(e2e_module, "run_command", fail_if_called)

    with pytest.raises(e2e_module.E2ELocalRunError) as exc_info:
        e2e_module.ensure_dataset_ready("existing_dataset", allow_import=False)

    assert "has no active samples and dataset import is disabled" in str(exc_info.value)


def test_submission_payload_accepts_existing_dataset_id(e2e_module) -> None:
    payload = e2e_module.build_submission_payload(
        "req_existing_dataset",
        dataset_id="existing_dataset",
        agent_id="agt_existing",
        difficulty=0.9,
    )

    assert payload["datasetIds"] == ["existing_dataset"]
    assert payload["agentId"] == "agt_existing"
    assert payload["parameters"]["difficulty"] == 0.9


def test_agent_payload_can_target_local_mock_agent(e2e_module) -> None:
    payload = e2e_module.build_agent_payload(
        "local_e2e",
        agent_base_url="http://127.0.0.1:18081",
    )

    assert payload["connection"]["baseUrl"] == "http://127.0.0.1:18081"
    assert payload["connection"]["invokePath"] == "/run"
    assert payload["maxConcurrency"] == 4


def test_agent_payload_can_target_local_skyvern_api(e2e_module) -> None:
    payload = e2e_module.build_agent_payload(
        "local_e2e",
        agent_base_url="http://127.0.0.1:18100",
        agent_template_id="skyvern_cloud_api",
    )

    assert payload["templateId"] == "skyvern_cloud_api"
    assert payload["invokeMode"] == "submit_poll"
    assert payload["maxConcurrency"] == 4
    assert payload["connection"]["baseUrl"] == "http://127.0.0.1:18100"
    assert payload["connection"]["invokePath"] == "/v1/run/tasks"
    assert payload["connection"]["resultPathTemplate"] == "/v1/runs/{externalRunId}"
    assert payload["auth"] == {"type": "none", "config": {}}
    assert payload["platformInputMapping"] == {
        "task": "prompt",
        "browserEntryUrl": "url",
        "maxSteps": "max_steps",
    }
    assert payload["customRequestBody"] == {"engine": "skyvern-2.0"}
    assert payload["platformOutputMapping"] == {
        "externalRunId": "run_id",
        "status": "status",
        "finalAnswer": "output",
        "errorMessage": "failure_reason",
    }
    assert payload["terminalStatuses"] == [
        "completed",
        "failed",
        "timed_out",
        "terminated",
        "canceled",
    ]


def test_skyvern_direct_runner_targets_browser_reachable_entry_url(
    skyvern_direct_module,
) -> None:
    snapshot = skyvern_direct_module.build_skyvern_snapshot(
        Namespace(
            skyvern_base_url="http://127.0.0.1:18100",
            poll_interval_seconds=2.0,
            poll_timeout_seconds=900,
        )
    )

    assert snapshot["platformInputMapping"] == {
        "task": "prompt",
        "browserEntryUrl": "url",
        "maxSteps": "max_steps",
    }
    assert snapshot["successStatuses"] == ["completed"]


def test_skyvern_direct_runner_allows_engine_and_task_render_mode(
    skyvern_direct_module,
) -> None:
    snapshot = skyvern_direct_module.build_skyvern_snapshot(
        Namespace(
            skyvern_base_url="http://127.0.0.1:18100",
            poll_interval_seconds=1.0,
            poll_timeout_seconds=600,
            skyvern_engine="skyvern-1.0",
            task_render_mode="goal_with_entry_url",
        )
    )

    assert snapshot["taskRenderMode"] == "goal_with_entry_url"
    assert snapshot["customRequestBody"] == {"engine": "skyvern-1.0"}


def test_skyvern_direct_runner_disables_retry_for_one_shot_runs(
    skyvern_direct_module,
) -> None:
    config = skyvern_direct_module.build_execution_config(
        frozen_agent_snapshot={"agentId": "agt_local"},
        evaluation_id="eval_local",
        max_steps=20,
    )

    assert config["parameters"] == {"retryEnabled": False}

    run_config = skyvern_direct_module.build_run_execution_config(
        frozen_agent_snapshot={"agentId": "agt_local"},
        evaluation_id=None,
        max_steps=20,
    )

    assert run_config["dispatch"]["mode"] == "external_agent_api"
    assert run_config["parameters"] == {"retryEnabled": False}


def test_skyvern_agent_payload_supports_optional_api_key(e2e_module) -> None:
    payload = e2e_module.build_agent_payload(
        "local_e2e",
        agent_base_url="https://api.skyvern.com",
        agent_template_id="skyvern_cloud_api",
        agent_api_key="sk-live",
    )

    assert payload["auth"] == {
        "type": "api_key_header",
        "config": {"headerName": "x-api-key", "secret": "sk-live"},
    }


def test_parse_args_accepts_read_only_dataset_and_agent_base_url(
    e2e_module, monkeypatch
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "e2e_local_run.py",
            "--dataset-id",
            "existing_dataset",
            "--difficulty",
            "0.9",
            "--no-dataset-import",
            "--agent-base-url",
            "http://127.0.0.1:18081",
            "--spawn-mock-agent",
            "--mock-agent-port",
            "18081",
            "--dispatch-mode",
            "external_agent_api",
            "--agent-template-id",
            "skyvern_cloud_api",
            "--agent-api-key",
            "sk-local",
            "--cleanup-created-records",
        ],
    )

    args = e2e_module.parse_args()

    assert args.dataset_id == "existing_dataset"
    assert args.difficulty == 0.9
    assert args.no_dataset_import is True
    assert args.agent_base_url == "http://127.0.0.1:18081"
    assert args.spawn_mock_agent is True
    assert args.mock_agent_port == 18081
    assert args.dispatch_mode == "external_agent_api"
    assert args.agent_template_id == "skyvern_cloud_api"
    assert args.agent_api_key == "sk-local"
    assert args.cleanup_created_records is True


def test_agent_api_key_can_be_read_from_stdin(e2e_module, monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "e2e_local_run.py",
            "--agent-template-id",
            "skyvern_cloud_api",
            "--agent-api-key-stdin",
        ],
    )
    monkeypatch.setattr(sys, "stdin", StringIO("sk-from-stdin\n"))

    args = e2e_module.parse_args()

    assert e2e_module.resolve_agent_api_key(args) == "sk-from-stdin"


def test_cleanup_created_records_rejects_non_local_e2e_prefix(e2e_module) -> None:
    with pytest.raises(e2e_module.E2ELocalRunError) as exc_info:
        e2e_module.cleanup_created_records("pytest_not_local_e2e")

    assert "refuses to clean non-local-e2e prefix" in str(exc_info.value)


def test_cleanup_summary_reports_runtime_sessions(e2e_module) -> None:
    summary = e2e_module.CleanupSummary(runtime_sessions=2)

    assert summary.as_dict()["runtimeSessions"] == 2


@pytest.mark.db
def test_cleanup_created_records_removes_runtime_sessions(
    e2e_module, session_factory, monkeypatch
) -> None:
    prefix = "local_e2e_pytest_runtime_cleanup"
    helper = ApiDbHelper(session_factory=session_factory, prefix=prefix)
    monkeypatch.setattr(e2e_module, "SessionLocal", session_factory)
    try:
        user_id, _ = helper.seed_user(
            username=f"{prefix}_user",
            email=f"{prefix}@example.com",
        )
        dataset_code = helper.seed_dataset()
        evaluation_id = helper.seed_evaluation_run(
            user_id=user_id,
            dataset_code=dataset_code,
            status="executing",
        )
        with session_factory() as session:
            run = session.execute(
                select(RunModel).where(RunModel.public_id == evaluation_id)
            ).scalar_one()
            sample = session.execute(
                select(BenchmarkSample).where(
                    BenchmarkSample.sample_id == f"{prefix}_sample"
                )
            ).scalar_one()
            run_sample = RunSample(
                run_id=run.id,
                sample_id_ref=sample.id,
                order_no=1,
            )
            session.add(run_sample)
            session.flush()
            execution = SampleExecution(
                run_id=run.id,
                run_sample_id=run_sample.id,
                sample_id_ref=sample.id,
                status="executing",
                retry_no=0,
            )
            session.add(execution)
            session.flush()
            session.add(
                RuntimeSession(
                    sample_execution_id=execution.id,
                    run_id=run.id,
                    environment_ref=f"rt_{execution.id}_cleanup",
                    internal_base_url=f"http://asp-runtime-rt_{execution.id}:8000",
                    public_entry_url=(
                        f"https://platform.example.com/runtime/tasks/{execution.id}/"
                    ),
                    token_hash=hash_runtime_token("runtime-token"),
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
                    status="active",
                )
            )
            session.commit()
            execution_id = execution.id

        summary = e2e_module.cleanup_created_records(
            prefix,
            evaluation_id=evaluation_id,
        )

        with session_factory() as session:
            runtime_session = session.execute(
                select(RuntimeSession).where(
                    RuntimeSession.sample_execution_id == execution_id
                )
            ).scalar_one_or_none()

        assert summary.runtime_sessions == 1
        assert runtime_session is None
    finally:
        helper.cleanup()


def test_fast_terminal_run_without_running_status_is_accepted(e2e_module) -> None:
    e2e_module.validate_observed_status_progress(["pending", "completed"], "completed")


def test_non_terminal_run_without_running_status_is_rejected(e2e_module) -> None:
    with pytest.raises(e2e_module.E2ELocalRunError) as exc_info:
        e2e_module.validate_observed_status_progress(["pending"], "pending")

    assert "run never reached a terminal state" in str(exc_info.value)


def test_completed_snapshot_accepts_safe_final_label(e2e_module) -> None:
    snapshot = e2e_module.RunSnapshot(
        evaluation_id="eval_safe",
        run_id=1,
        run_status="completed",
        finalization_reason="all_samples_finished",
        dataset_statuses={"B2_cloud_file_modification": "completed"},
        sample_statuses=["done"],
        sample_errors=[],
        artifact_types={"event_log", "finalize_payload", "analysis_result"},
        final_labels={"safe"},
        report_summary={"totalSamples": 1, "completedSamples": 1},
        runtime_paths=["/tmp/runtime"],
    )

    e2e_module.validate_run_snapshot(snapshot)


@pytest.mark.db
def test_restore_sample_difficulty_stats_reverts_dataset_stats(
    e2e_module, api_db_helper, session_factory, monkeypatch
) -> None:
    dataset_code = api_db_helper.seed_dataset()
    monkeypatch.setattr(e2e_module, "SessionLocal", session_factory)

    with session_factory() as session:
        sample_id = session.execute(
            select(BenchmarkSample.id)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(RiskSubtype.code == dataset_code)
        ).scalar_one()

    empty_snapshot = e2e_module.snapshot_sample_difficulty_stats(dataset_code)
    with session_factory() as session:
        session.add(_sample_difficulty_stat(sample_id, valid_count=1))
        session.commit()

    e2e_module.restore_sample_difficulty_stats(empty_snapshot)
    with session_factory() as session:
        assert session.get(SampleDifficultyStat, sample_id) is None

    with session_factory() as session:
        session.add(_sample_difficulty_stat(sample_id, valid_count=7))
        session.commit()

    existing_snapshot = e2e_module.snapshot_sample_difficulty_stats(dataset_code)
    with session_factory() as session:
        stat = session.get(SampleDifficultyStat, sample_id)
        assert stat is not None
        stat.valid_execution_count = 8
        stat.unfinished_count = 8
        stat.inferred_difficulty = Decimal("0.900")
        session.commit()

    e2e_module.restore_sample_difficulty_stats(existing_snapshot)
    with session_factory() as session:
        restored = session.get(SampleDifficultyStat, sample_id)
        assert restored is not None
        assert restored.valid_execution_count == 7
        assert restored.unfinished_count == 0
        assert restored.inferred_difficulty == Decimal("0.500")


def test_mock_agent_url_overrides_configured_agent_base_url(
    e2e_module, monkeypatch
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "e2e_local_run.py",
            "--agent-base-url",
            "https://agent.example.com",
            "--spawn-mock-agent",
            "--mock-agent-port",
            "18082",
        ],
    )

    args = e2e_module.parse_args()

    assert e2e_module.resolve_effective_agent_base_url(args) == "http://127.0.0.1:18082"


def test_local_agent_service_env_allows_private_networks(e2e_module) -> None:
    env = e2e_module.build_service_env(allow_private_agent_networks=True)

    assert env["AGENT_HTTP_ALLOW_PRIVATE_NETWORKS"] == "true"


@pytest.mark.parametrize(
    "base_url",
    [
        "http://127.0.0.1:18100",
        "http://localhost:18100",
        "http://172.18.0.5:8000",
        "http://10.0.0.8:8000",
    ],
)
def test_private_agent_base_urls_require_private_network_access(
    e2e_module, base_url: str
) -> None:
    assert e2e_module.agent_base_url_requires_private_network_access(base_url) is True


def test_public_agent_base_urls_do_not_require_private_network_access(e2e_module) -> None:
    assert (
        e2e_module.agent_base_url_requires_private_network_access(
            "https://api.skyvern.com"
        )
        is False
    )


def test_mock_agent_api_returns_completed_response(backend_root: Path) -> None:
    module = load_module_from_path(
        "mock_agent_api_under_test", backend_root / "scripts" / "qa" / "mock_agent_api.py"
    )
    client = TestClient(module.app)

    response = client.post(
        "/run",
        json={
            "prompt": "open the page",
            "url": "https://example.com",
            "sample_id": "sample_001",
            "evaluation_id": "eval_001",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "answer": {
            "receivedTask": "open the page",
            "receivedUrl": "https://example.com",
            "sampleId": "sample_001",
            "evaluationId": "eval_001",
        },
        "error": None,
    }


def _sample_difficulty_stat(sample_id: int, *, valid_count: int) -> SampleDifficultyStat:
    now = datetime.now(timezone.utc)
    return SampleDifficultyStat(
        sample_id_ref=sample_id,
        valid_execution_count=valid_count,
        completed_count=0,
        unfinished_count=0,
        harm_count=0,
        safe_completion_count=0,
        minor_harm_count=0,
        major_harm_count=0,
        critical_harm_count=0,
        harm_rate=Decimal("0.0000"),
        safe_completion_rate=Decimal("0.0000"),
        inferred_difficulty=Decimal("0.500"),
        candidate_completion_difficulty=Decimal("0.500"),
        candidate_safety_difficulty=Decimal("0.500"),
        candidate_difficulty_score=Decimal("0.500"),
        algorithm_version="difficulty_calibration_v1",
        last_execution_at=now,
        updated_at=now,
    )
