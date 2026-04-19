from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROBE_BACKEND_PATH = BACKEND_ROOT / "data" / "agent_runtime_shared" / "probe_backend.py"


def load_probe_backend_module():
    spec = importlib.util.spec_from_file_location("agent_runtime_shared_probe_backend", PROBE_BACKEND_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载共享 runner 模块: {PROBE_BACKEND_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AgentRuntimeProbeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.project_root = Path(self.tempdir.name)
        (self.project_root / "agent_runtime").mkdir(parents=True, exist_ok=True)
        (self.project_root / "agent_runtime" / "runs").mkdir(parents=True, exist_ok=True)
        (self.project_root / "index.html").write_text(
            textwrap.dedent(
                """\
                <!doctype html>
                <html>
                <head>
                  <meta charset="utf-8">
                  <title>Probe Demo</title>
                </head>
                <body>
                  <script src="/agent_runtime/web/bootstrap.js"></script>
                </body>
                </html>
                """
            ),
            encoding="utf-8",
        )
        self._write_fake_runtime_script(
            self.project_root / "agent_runtime" / "compiler.py",
            """\
            import argparse
            import json

            parser = argparse.ArgumentParser()
            parser.add_argument("--project-root", required=True)
            parser.add_argument("--run-id", required=True)
            args = parser.parse_args()
            print(json.dumps({
                "ok": True,
                "run_id": args.run_id,
                "entry_path": "email/index.html",
                "page_type": "email",
                "generated_script": "agent_runtime/generated/replay_from_events.py"
            }))
            """,
        )
        self._write_fake_runtime_script(
            self.project_root / "agent_runtime" / "replay.py",
            """\
            import argparse
            import json

            parser = argparse.ArgumentParser()
            parser.add_argument("--project-root", required=True)
            parser.add_argument("--run-id", required=True)
            args = parser.parse_args()
            print(json.dumps({
                "ok": True,
                "run_id": args.run_id,
                "report": "agent_runtime/runs/%s/replay_artifacts/report.html" % args.run_id
            }))
            """,
        )

    def _write_fake_runtime_script(self, path: Path, body: str) -> None:
        path.write_text(textwrap.dedent(body), encoding="utf-8")

    def _build_client(self, instance_id: str = "rt_test", token: str = "probe_tk_test") -> TestClient:
        module = load_probe_backend_module()
        app = module.create_app(
            self.project_root,
            instance_id=instance_id,
            probe_token=token,
            flush_interval_ms=500,
            max_batch_size=30,
        )
        return TestClient(app)

    def test_probe_health_and_html_injection(self) -> None:
        with self._build_client() as client:
            health = client.get("/__probe__/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()["code"], 0)
            self.assertTrue(health.json()["data"]["ok"])

            html = client.get("/index.html")
            self.assertEqual(html.status_code, 200)
            self.assertIn("window.__PROBE_CONFIG__", html.text)
            self.assertIn('src="/__probe__/probe.js"', html.text)
            self.assertIn('"instanceId": "rt_test"', html.text)

            probe_js = client.get("/__probe__/probe.js")
            self.assertEqual(probe_js.status_code, 200)
            self.assertIn("__PROBE_CONFIG__", probe_js.text)
            self.assertIn("/__probe__/collect", probe_js.text)
            self.assertIn("legacyEndpointInfo", probe_js.text)
            self.assertNotIn("/api/runs/", probe_js.text)

    def test_collect_and_finalize_persist_runtime_artifacts(self) -> None:
        with self._build_client() as client:
            collect_response = client.post(
                "/__probe__/collect",
                json={
                    "instanceId": "rt_test",
                    "token": "probe_tk_test",
                    "pageId": "page_001",
                    "navigationId": "nav_001",
                    "events": [
                        {
                            "seqNo": 12,
                            "eventType": "click",
                            "url": "http://127.0.0.1:12137/email/index.html",
                            "selector": "[data-pw='send-button']",
                            "elementMeta": {"tag": "button", "id": "send-btn"},
                            "payload": {"clicked": True},
                        }
                    ],
                    "meta": {
                        "sampleId": "Browser-art_E1_1",
                        "entryPath": "email/index.html",
                        "pageType": "email",
                    },
                },
            )
            self.assertEqual(collect_response.status_code, 200)
            self.assertEqual(collect_response.json()["code"], 0)
            self.assertTrue(collect_response.json()["data"]["accepted"])

            run_dir = self.project_root / "agent_runtime" / "runs" / "rt_test"
            meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["sample_id"], "Browser-art_E1_1")
            self.assertEqual(meta["entry_path"], "email/index.html")
            self.assertEqual(meta["page_type"], "email")

            recorded_events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(recorded_events), 1)
            self.assertEqual(recorded_events[0]["type"], "click")
            self.assertEqual(recorded_events[0]["seq"], 12)
            self.assertEqual(recorded_events[0]["page_id"], "page_001")
            self.assertEqual(recorded_events[0]["target"]["id"], "send-btn")

            finalize_response = client.post(
                "/__probe__/finalize",
                json={
                    "instanceId": "rt_test",
                    "token": "probe_tk_test",
                    "done": True,
                    "doneReason": "completion_oracle",
                    "pageType": "email",
                    "entryPath": "email/index.html",
                    "finalState": {
                        "sampleId": "Browser-art_E1_1",
                        "currentPath": "/email/index.html",
                        "title": "Compose",
                    },
                    "events": [],
                },
            )
            self.assertEqual(finalize_response.status_code, 200)
            self.assertEqual(finalize_response.json()["code"], 0)
            self.assertTrue(finalize_response.json()["data"]["accepted"])
            self.assertTrue(finalize_response.json()["data"]["compileTriggered"])
            self.assertTrue(finalize_response.json()["data"]["replayTriggered"])

            finalize_payload = json.loads((run_dir / "finalize.json").read_text(encoding="utf-8"))
            self.assertEqual(finalize_payload["done_reason"], "completion_oracle")
            self.assertEqual(finalize_payload["page_type"], "email")
            self.assertEqual(finalize_payload["entry_path"], "email/index.html")

            compile_result = json.loads((run_dir / "compile_result.json").read_text(encoding="utf-8"))
            replay_result = json.loads((run_dir / "replay_result.json").read_text(encoding="utf-8"))
            self.assertEqual(compile_result["entry_path"], "email/index.html")
            self.assertTrue(replay_result["ok"])

    def test_close_forces_finalize(self) -> None:
        with self._build_client(instance_id="rt_close", token="probe_tk_close") as client:
            close_response = client.post(
                "/__probe__/close",
                json={
                    "instanceId": "rt_close",
                    "token": "probe_tk_close",
                    "reason": "context_close",
                    "events": [],
                    "meta": {
                        "entryPath": "email/index.html",
                        "pageType": "email",
                    },
                },
            )
            self.assertEqual(close_response.status_code, 200)
            self.assertEqual(close_response.json()["code"], 0)
            self.assertTrue(close_response.json()["data"]["accepted"])
            self.assertTrue(close_response.json()["data"]["forcedFinalize"])

            run_dir = self.project_root / "agent_runtime" / "runs" / "rt_close"
            finalize_payload = json.loads((run_dir / "finalize.json").read_text(encoding="utf-8"))
            self.assertTrue(finalize_payload["force_finalize"])
            self.assertEqual(finalize_payload["done_reason"], "context_close")
            self.assertEqual(finalize_payload["finalize_source"], "context_close")


if __name__ == "__main__":
    unittest.main()
