from __future__ import annotations

import json

import httpx
import pytest

from app.modules.agents.invocation import (
    AgentInvocationClient,
    build_agent_request_body,
    read_json_path,
)


def test_read_json_path_reads_nested_response_values() -> None:
    payload = {"data": {"runId": "run_1", "result": {"answer": "done"}}}

    assert read_json_path(payload, "data.runId") == "run_1"
    assert read_json_path(payload, "data.result.answer") == "done"
    assert read_json_path(payload, "data.missing") is None


def test_build_agent_request_body_rejects_mapping_conflicts() -> None:
    with pytest.raises(ValueError):
        build_agent_request_body(
            custom_request_body={"prompt": "fixed"},
            platform_input_mapping={"task": "prompt"},
            platform_values={"task": "dynamic"},
        )


@pytest.mark.asyncio
async def test_sync_response_invocation_posts_mapped_payload_and_parses_result() -> (
    None
):
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        assert request.headers["authorization"] == "Bearer sk-demo"
        assert request.url == "https://agent.example.com/v1/run"
        assert json.loads(request.content.decode("utf-8")) == {
            "engine": "demo",
            "prompt": "do task",
            "url": "https://runtime.example.com",
        }
        return httpx.Response(200, json={"status": "completed", "answer": "ok"})

    client = AgentInvocationClient(transport=httpx.MockTransport(handler))

    result = await client.invoke(
        agent_snapshot={
            "invokeMode": "sync_response",
            "connection": {
                "baseUrl": "https://agent.example.com",
                "invokePath": "/v1/run",
                "requestTimeoutSeconds": 30,
            },
            "auth": {"type": "bearer", "credentialRef": "secret_1"},
            "platformInputMapping": {"task": "prompt", "entryUrl": "url"},
            "customRequestBody": {"engine": "demo"},
            "platformOutputMapping": {"status": "status", "finalAnswer": "answer"},
            "terminalStatuses": ["completed", "failed"],
            "successStatuses": ["completed"],
        },
        credential_payload={"token": "sk-demo"},
        platform_values={"task": "do task", "entryUrl": "https://runtime.example.com"},
    )

    assert len(seen_requests) == 1
    assert result.passed is True
    assert result.status == "completed"
    assert result.final_answer == "ok"


@pytest.mark.asyncio
async def test_submit_poll_invocation_polls_until_terminal_status() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.method == "POST":
            return httpx.Response(
                200, json={"data": {"runId": "run_1", "status": "queued"}}
            )
        return httpx.Response(
            200,
            json={"data": {"runId": "run_1", "status": "completed", "answer": "ok"}},
        )

    client = AgentInvocationClient(transport=httpx.MockTransport(handler))

    result = await client.invoke(
        agent_snapshot={
            "invokeMode": "submit_poll",
            "connection": {
                "baseUrl": "https://agent.example.com",
                "invokePath": "/v1/runs",
                "resultPathTemplate": "/v1/runs/{externalRunId}",
                "requestTimeoutSeconds": 30,
                "pollIntervalSeconds": 0,
                "pollTimeoutSeconds": 5,
            },
            "auth": {"type": "none", "credentialRef": None},
            "platformInputMapping": {"task": "prompt"},
            "customRequestBody": {},
            "platformOutputMapping": {
                "externalRunId": "data.runId",
                "status": "data.status",
                "finalAnswer": "data.answer",
            },
            "terminalStatuses": ["completed", "failed"],
            "successStatuses": ["completed"],
        },
        credential_payload={},
        platform_values={"task": "do task"},
    )

    assert calls == ["/v1/runs", "/v1/runs/run_1"]
    assert result.passed is True
    assert result.external_run_id == "run_1"
    assert result.final_answer == "ok"
