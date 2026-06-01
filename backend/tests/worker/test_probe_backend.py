from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.worker.runtime.probe_backend import (
    build_probe_config,
    create_app,
    inject_probe_assets,
)


def test_probe_injection_loads_dataset_bootstrap_after_core_probe() -> None:
    injected = inject_probe_assets(
        "<html><head></head><body></body></html>",
        build_probe_config(
            instance_id="rt_123_test",
            probe_token="probe-token",
            flush_interval_ms=1200,
            max_batch_size=12,
        ),
    )

    core_script = '<script src="/__probe__/probe.js"></script>'
    bootstrap_script = '<script src="/agent_runtime/web/bootstrap.js"></script>'
    assert core_script in injected
    assert bootstrap_script in injected
    assert injected.index(core_script) < injected.index(bootstrap_script)


@pytest.mark.asyncio
async def test_legacy_observable_api_events_route_records_events(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    app = create_app(
        project_root,
        instance_id="rt_123_test",
        probe_token="probe-token",
    )
    payload = json.dumps(
        {
            "events": [
                {
                    "type": "click",
                    "seq": 1,
                    "target": {"tag": "button", "text": "Tweet"},
                }
            ],
            "meta": {"sample_id": "Sample_1", "page_type": "twitter"},
        }
    ).encode("utf-8")
    messages: list[dict[str, Any]] = []
    receive_count = 0

    async def receive() -> dict[str, Any]:
        nonlocal receive_count
        receive_count += 1
        if receive_count == 1:
            return {"type": "http.request", "body": payload, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/runs/rt_123_test/events",
            "raw_path": b"/api/runs/rt_123_test/events",
            "query_string": b"",
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(payload)).encode("ascii")),
            ],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        },
        receive,
        send,
    )

    response_start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    response_body = next(
        message for message in messages if message["type"] == "http.response.body"
    )
    assert response_start["status"] == 200
    assert json.loads(response_body["body"])["batch_events"] == 1
    events_path = (
        project_root / "agent_runtime" / "runs" / "rt_123_test" / "events.jsonl"
    )
    assert events_path.read_text(encoding="utf-8").count("\n") == 1
