from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.worker


def load_probe_backend_module():
    from app.worker.runtime import probe_backend

    return probe_backend


def write_fake_runtime_script(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body), encoding="utf-8")


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "agent_runtime" / "runs").mkdir(parents=True, exist_ok=True)
    (root / "index.html").write_text(
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
    write_fake_runtime_script(
        root / "agent_runtime" / "compiler.py",
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
    write_fake_runtime_script(
        root / "agent_runtime" / "replay.py",
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
    return root


def build_client(project_root: Path, *, instance_id: str = "rt_test", token: str = "probe_tk_test") -> TestClient:
    module = load_probe_backend_module()
    app = module.create_app(
        project_root,
        instance_id=instance_id,
        probe_token=token,
        flush_interval_ms=500,
        max_batch_size=30,
    )
    return TestClient(app)


def test_probe_health_and_html_injection(project_root: Path) -> None:
    with build_client(project_root) as client:
        health = client.get("/__probe__/health")
        assert health.status_code == 200
        assert health.json()["code"] == 0
        assert health.json()["data"]["ok"] is True

        html = client.get("/index.html")
        assert html.status_code == 200
        assert "window.__PROBE_CONFIG__" in html.text
        assert 'src="/__probe__/probe.js"' in html.text
        assert '"instanceId": "rt_test"' in html.text

        probe_js = client.get("/__probe__/probe.js")
        assert probe_js.status_code == 200
        assert "__PROBE_CONFIG__" in probe_js.text
        assert "/__probe__/collect" in probe_js.text
        assert "legacyEndpointInfo" in probe_js.text
        assert "/api/runs/" not in probe_js.text


def test_collect_and_finalize_persist_runtime_artifacts(project_root: Path) -> None:
    with build_client(project_root) as client:
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
        assert collect_response.status_code == 200
        assert collect_response.json()["code"] == 0
        assert collect_response.json()["data"]["accepted"] is True

        run_dir = project_root / "agent_runtime" / "runs" / "rt_test"
        meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
        assert meta["sample_id"] == "Browser-art_E1_1"
        assert meta["entry_path"] == "email/index.html"
        assert meta["page_type"] == "email"

        recorded_events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(recorded_events) == 1
        assert recorded_events[0]["type"] == "click"
        assert recorded_events[0]["seq"] == 12
        assert recorded_events[0]["page_id"] == "page_001"
        assert recorded_events[0]["target"]["id"] == "send-btn"

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
        assert finalize_response.status_code == 200
        assert finalize_response.json()["code"] == 0
        assert finalize_response.json()["data"]["accepted"] is True
        assert finalize_response.json()["data"]["compileTriggered"] is True
        assert finalize_response.json()["data"]["replayTriggered"] is True

        finalize_payload = json.loads((run_dir / "finalize.json").read_text(encoding="utf-8"))
        assert finalize_payload["done_reason"] == "completion_oracle"
        assert finalize_payload["page_type"] == "email"
        assert finalize_payload["entry_path"] == "email/index.html"

        compile_result = json.loads((run_dir / "compile_result.json").read_text(encoding="utf-8"))
        replay_result = json.loads((run_dir / "replay_result.json").read_text(encoding="utf-8"))
        assert compile_result["entry_path"] == "email/index.html"
        assert replay_result["ok"] is True


def test_close_forces_finalize(project_root: Path) -> None:
    with build_client(project_root, instance_id="rt_close", token="probe_tk_close") as client:
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
        assert close_response.status_code == 200
        assert close_response.json()["code"] == 0
        assert close_response.json()["data"]["accepted"] is True
        assert close_response.json()["data"]["forcedFinalize"] is True

        run_dir = project_root / "agent_runtime" / "runs" / "rt_close"
        finalize_payload = json.loads((run_dir / "finalize.json").read_text(encoding="utf-8"))
        assert finalize_payload["force_finalize"] is True
        assert finalize_payload["done_reason"] == "context_close"
        assert finalize_payload["finalize_source"] == "context_close"
