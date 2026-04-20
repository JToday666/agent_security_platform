from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = BACKEND_ROOT / "scripts" / "e2e_local_run.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("scripts_e2e_local_run", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本模块: {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class E2ELocalRunScriptTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_script_module()

    def test_build_submission_payload_uses_b2_defaults(self) -> None:
        payload = self.module.build_submission_payload("req_demo")

        self.assertEqual(payload["datasetIds"], ["B2_cloud_file_modification"])
        self.assertEqual(payload["submitMethod"], "api")
        self.assertEqual(payload["api"]["baseUrl"], "https://example.com/agent")
        self.assertEqual(payload["parameters"]["difficulty"], 0.5)
        self.assertEqual(payload["parameters"]["timeoutMinutes"], 20)
        self.assertFalse(payload["parameters"]["retryEnabled"])
        self.assertEqual(payload["requestId"], "req_demo")

    def test_is_terminal_run_status_recognizes_backend_terminal_states(self) -> None:
        self.assertTrue(self.module.is_terminal_run_status("completed"))
        self.assertTrue(self.module.is_terminal_run_status("failed"))
        self.assertTrue(self.module.is_terminal_run_status("terminated"))
        self.assertTrue(self.module.is_terminal_run_status("canceled"))
        self.assertFalse(self.module.is_terminal_run_status("running"))

    def test_ensure_dataset_ready_skips_bootstrap_when_samples_exist(self) -> None:
        with patch.object(self.module, "count_active_samples", side_effect=[6]) as count_mock, \
             patch.object(self.module, "run_command") as run_command_mock:
            result = self.module.ensure_dataset_ready()

        self.assertEqual(result, 6)
        self.assertEqual(count_mock.call_count, 1)
        run_command_mock.assert_not_called()

    def test_ensure_dataset_ready_bootstraps_when_dataset_missing(self) -> None:
        with patch.object(self.module, "count_active_samples", side_effect=[0, 6]) as count_mock, \
             patch.object(self.module, "run_command") as run_command_mock:
            result = self.module.ensure_dataset_ready()

        self.assertEqual(result, 6)
        self.assertEqual(count_mock.call_count, 2)
        self.assertEqual(run_command_mock.call_count, 2)

    def test_resolve_submission_difficulty_keeps_preferred_when_bucket_has_samples(self) -> None:
        with patch.object(self.module, "count_matching_samples_for_difficulty", return_value=2) as match_mock, \
             patch.object(self.module, "list_active_difficulty_scores") as list_mock:
            resolved, adjusted = self.module.resolve_submission_difficulty("B2_cloud_file_modification", 0.5)

        self.assertEqual(resolved, 0.5)
        self.assertFalse(adjusted)
        match_mock.assert_called_once_with("B2_cloud_file_modification", 0.5)
        list_mock.assert_not_called()

    def test_resolve_submission_difficulty_falls_back_to_nearest_available_score(self) -> None:
        with patch.object(self.module, "count_matching_samples_for_difficulty", return_value=0) as match_mock, \
             patch.object(self.module, "list_active_difficulty_scores", return_value=[0.35, 0.675, 1.0]) as list_mock:
            resolved, adjusted = self.module.resolve_submission_difficulty("B2_cloud_file_modification", 0.5)

        self.assertEqual(resolved, 0.35)
        self.assertTrue(adjusted)
        match_mock.assert_called_once_with("B2_cloud_file_modification", 0.5)
        list_mock.assert_called_once_with("B2_cloud_file_modification")

    def test_validate_run_snapshot_requires_done_sample_and_core_artifacts(self) -> None:
        snapshot = self.module.RunSnapshot(
            evaluation_id="eval_demo",
            run_id=1,
            run_status="completed",
            finalization_reason=None,
            dataset_statuses={"B2_cloud_file_modification": "completed"},
            sample_statuses=["done", "error"],
            sample_errors=["RuntimeError: demo"],
            artifact_types={"event_log", "compile_result", "replay_result"},
            final_labels={"needs_review"},
            report_summary={"totalSamples": 1},
            runtime_paths=["runtime://demo"],
        )

        self.module.validate_run_snapshot(snapshot)

        missing_artifacts = self.module.RunSnapshot(
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
        with self.assertRaises(self.module.E2ELocalRunError):
            self.module.validate_run_snapshot(missing_artifacts)

        no_done = self.module.RunSnapshot(
            evaluation_id="eval_demo",
            run_id=1,
            run_status="completed",
            finalization_reason=None,
            dataset_statuses={"B2_cloud_file_modification": "completed"},
            sample_statuses=["error"],
            sample_errors=["boom"],
            artifact_types={"event_log", "compile_result", "replay_result"},
            final_labels=set(),
            report_summary={"totalSamples": 1},
            runtime_paths=[],
        )
        with self.assertRaises(self.module.E2ELocalRunError):
            self.module.validate_run_snapshot(no_done)

    def test_poll_evaluation_detail_uses_auth_headers(self) -> None:
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
                return DummyResponse({"code": 0, "data": {"status": "completed"}, "message": "success"})

        client = DummyClient()

        detail, seen_statuses = self.module.poll_evaluation_detail(
            client,
            "eval_demo",
            timeout_seconds=0.1,
            poll_interval_seconds=0.01,
            headers={"Authorization": "Bearer demo"},
        )

        self.assertEqual(detail["status"], "completed")
        self.assertEqual(seen_statuses, ["completed"])
        self.assertEqual(client.headers_seen, [{"Authorization": "Bearer demo"}])


if __name__ == "__main__":
    unittest.main()
