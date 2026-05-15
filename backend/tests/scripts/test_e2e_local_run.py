from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from tests.helpers.scripts import load_module_from_path

pytestmark = pytest.mark.scripts


def load_e2e_module(backend_root: Path):
    return load_module_from_path(
        f"scripts_e2e_local_run_{uuid4().hex}",
        backend_root / "scripts" / "qa" / "e2e_local_run.py",
    )


def test_parse_args_supports_spawn_services(
    backend_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_e2e_module(backend_root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "e2e_local_run.py",
            "--spawn-services",
            "--base-url",
            "http://127.0.0.1:9000",
            "--poll-timeout",
            "60",
            "--poll-interval",
            "1.5",
        ],
    )

    args = module.parse_args()

    assert args.spawn_services is True
    assert args.base_url == "http://127.0.0.1:9000"
    assert args.poll_timeout == 60
    assert args.poll_interval == 1.5


def test_build_submission_payload_uses_b2_defaults(backend_root: Path) -> None:
    module = load_e2e_module(backend_root)

    payload = module.build_submission_payload("req_demo", agent_id="agt_demo")

    assert payload["datasetIds"] == ["B2_cloud_file_modification"]
    assert payload["submitMethod"] == "api"
    assert payload["agentId"] == "agt_demo"
    assert payload["parameters"]["difficulty"] == 0.5
    assert payload["parameters"]["timeoutMinutes"] == 20
    assert payload["parameters"]["maxSteps"] == 30
    assert payload["leaderboardDisplayMode"] == "anonymous"
    assert "publicToLeaderboard" not in payload
    assert payload["requestId"] == "req_demo"


def test_is_terminal_run_status_recognizes_backend_terminal_states(
    backend_root: Path,
) -> None:
    module = load_e2e_module(backend_root)

    assert module.is_terminal_run_status("completed") is True
    assert module.is_terminal_run_status("failed") is True
    assert module.is_terminal_run_status("terminated") is True
    assert module.is_terminal_run_status("canceled") is True
    assert module.is_terminal_run_status("running") is False


def test_ensure_dataset_ready_skips_bootstrap_when_samples_exist(
    backend_root: Path,
) -> None:
    module = load_e2e_module(backend_root)

    with patch.object(
        module, "count_active_samples", side_effect=[6]
    ) as count_mock, patch.object(
        module,
        "run_command",
    ) as run_command_mock:
        result = module.ensure_dataset_ready()

    assert result == 6
    assert count_mock.call_count == 1
    run_command_mock.assert_not_called()


def test_ensure_dataset_ready_bootstraps_when_dataset_missing(
    backend_root: Path,
) -> None:
    module = load_e2e_module(backend_root)

    with patch.object(
        module, "count_active_samples", side_effect=[0, 6]
    ) as count_mock, patch.object(
        module,
        "run_command",
    ) as run_command_mock:
        result = module.ensure_dataset_ready()

    assert result == 6
    assert count_mock.call_count == 2
    assert run_command_mock.call_count == 2


def test_resolve_submission_difficulty_keeps_preferred_when_bucket_has_samples(
    backend_root: Path,
) -> None:
    module = load_e2e_module(backend_root)

    with patch.object(
        module, "count_matching_samples_for_difficulty", return_value=2
    ) as match_mock, patch.object(
        module,
        "list_active_difficulty_scores",
    ) as list_mock:
        resolved, adjusted = module.resolve_submission_difficulty(
            "B2_cloud_file_modification", 0.5
        )

    assert resolved == 0.5
    assert adjusted is False
    match_mock.assert_called_once_with("B2_cloud_file_modification", 0.5)
    list_mock.assert_not_called()


def test_resolve_submission_difficulty_falls_back_to_nearest_available_score(
    backend_root: Path,
) -> None:
    module = load_e2e_module(backend_root)

    with patch.object(
        module, "count_matching_samples_for_difficulty", return_value=0
    ) as match_mock, patch.object(
        module,
        "list_active_difficulty_scores",
        return_value=[0.35, 0.675, 1.0],
    ) as list_mock:
        resolved, adjusted = module.resolve_submission_difficulty(
            "B2_cloud_file_modification", 0.5
        )

    assert resolved == 0.35
    assert adjusted is True
    match_mock.assert_called_once_with("B2_cloud_file_modification", 0.5)
    list_mock.assert_called_once_with("B2_cloud_file_modification")


def test_validate_run_snapshot_requires_done_sample_and_core_artifacts(
    backend_root: Path,
) -> None:
    module = load_e2e_module(backend_root)
    snapshot = module.RunSnapshot(
        evaluation_id="eval_demo",
        run_id=1,
        run_status="completed",
        finalization_reason=None,
        dataset_statuses={"B2_cloud_file_modification": "completed"},
        sample_statuses=["done", "error"],
        sample_errors=["RuntimeError: demo"],
        artifact_types={"event_log", "finalize_payload", "analysis_result"},
        final_labels={"needs_review"},
        report_summary={"totalSamples": 1},
        runtime_paths=["runtime://demo"],
    )

    module.validate_run_snapshot(snapshot)

    missing_artifacts = module.RunSnapshot(
        evaluation_id="eval_demo",
        run_id=1,
        run_status="completed",
        finalization_reason=None,
        dataset_statuses={"B2_cloud_file_modification": "completed"},
        sample_statuses=["done"],
        sample_errors=[],
        artifact_types={"event_log"},
        final_labels={"needs_review"},
        report_summary={"totalSamples": 1},
        runtime_paths=[],
    )
    with pytest.raises(module.E2ELocalRunError):
        module.validate_run_snapshot(missing_artifacts)

    no_done = module.RunSnapshot(
        evaluation_id="eval_demo",
        run_id=1,
        run_status="completed",
        finalization_reason=None,
        dataset_statuses={"B2_cloud_file_modification": "completed"},
        sample_statuses=["error"],
        sample_errors=["boom"],
        artifact_types={"event_log", "finalize_payload", "analysis_result"},
        final_labels=set(),
        report_summary={"totalSamples": 1},
        runtime_paths=[],
    )
    with pytest.raises(module.E2ELocalRunError):
        module.validate_run_snapshot(no_done)


def test_poll_evaluation_detail_uses_auth_headers(backend_root: Path) -> None:
    module = load_e2e_module(backend_root)

    class DummyRequest:
        method = "GET"

        class URL:
            path = "/api/v1/evaluations/eval_demo"

        url = URL()

    class DummyResponse:
        def __init__(self, payload):
            self.status_code = 200
            self._payload = payload
            self.request = DummyRequest()
            self.text = ""

        def json(self):
            return self._payload

    class DummyClient:
        def __init__(self):
            self.headers_seen = []

        def get(self, path, headers=None):
            self.headers_seen.append(headers)
            return DummyResponse(
                {"code": 0, "data": {"status": "completed"}, "message": "success"}
            )

    client = DummyClient()

    detail, seen_statuses = module.poll_evaluation_detail(
        client,
        "eval_demo",
        timeout_seconds=0.1,
        poll_interval_seconds=0.01,
        headers={"Authorization": "Bearer demo"},
    )

    assert detail["status"] == "completed"
    assert seen_statuses == ["completed"]
    assert client.headers_seen == [{"Authorization": "Bearer demo"}]
