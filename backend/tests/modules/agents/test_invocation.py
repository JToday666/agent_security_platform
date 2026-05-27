from __future__ import annotations

import json
import logging
from typing import Any

import httpx
import pytest

from app.modules.agents.evidence import AgentInvocationEvidenceRecorder
from app.modules.agents.invocation import AgentInvocationError
from app.modules.agents.invocation import AgentInvocationClient
from app.modules.agents.invocation import _resolve_poll_timeout_seconds


def _submit_poll_snapshot(
    *,
    base_url: str,
    invoke_path: str,
    result_path_template: str,
    platform_input_mapping: dict[str, str],
    platform_output_mapping: dict[str, str],
    terminal_statuses: list[str],
    success_statuses: list[str],
    task_render_mode: str = "goal_only",
    auth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "invokeMode": "submit_poll",
        "connection": {
            "baseUrl": base_url,
            "invokePath": invoke_path,
            "resultPathTemplate": result_path_template,
            "requestTimeoutSeconds": 30,
            "pollIntervalSeconds": 0,
            "pollTimeoutSeconds": 30,
        },
        "auth": auth or {"type": "none"},
        "platformInputMapping": platform_input_mapping,
        "taskRenderMode": task_render_mode,
        "customRequestBody": {},
        "platformOutputMapping": platform_output_mapping,
        "terminalStatuses": terminal_statuses,
        "successStatuses": success_statuses,
    }


async def _invoke_with_responses(
    *,
    snapshot: dict[str, Any],
    credential_payload: dict[str, Any],
    submit_response: dict[str, Any],
    poll_response: dict[str, Any],
) -> tuple[Any, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(200, json=submit_response)
        return httpx.Response(200, json=poll_response)

    result = await AgentInvocationClient(httpx.MockTransport(handler)).invoke(
        agent_snapshot=snapshot,
        credential_payload=credential_payload,
        platform_values={
            "task": "Complete checkout",
            "entryUrl": "https://shop.example/cart",
            "timeoutSeconds": 120,
            "sampleId": "sample_001",
            "evaluationId": "eval_001",
            "maxSteps": 42,
        },
    )
    return result, requests


def _sync_snapshot(*, base_url: str = "https://api.example.com") -> dict[str, Any]:
    return {
        "agentId": "agt_evidence",
        "templateId": "custom_http",
        "invokeMode": "sync_response",
        "connection": {
            "baseUrl": base_url,
            "invokePath": "/run?api_key=query-secret&trace=abc",
            "requestTimeoutSeconds": 30,
        },
        "auth": {"type": "custom_header", "headerName": "X-Agent-Secret"},
        "platformInputMapping": {"task": "prompt", "sampleId": "sample_id"},
        "taskRenderMode": "goal_only",
        "customRequestBody": {
            "secret": "body-secret",
            "nested": {"password": "nested-password"},
        },
        "platformOutputMapping": {
            "status": "status",
            "finalAnswer": "answer",
            "errorMessage": "error",
        },
        "terminalStatuses": ["completed", "failed"],
        "successStatuses": ["completed"],
    }


def _platform_values() -> dict[str, Any]:
    return {
        "task": "Complete checkout",
        "entryUrl": "https://shop.example/cart",
        "timeoutSeconds": 120,
        "sampleId": "sample_001",
        "evaluationId": "eval_001",
        "maxSteps": 42,
    }


def _evidence_recorder(
    tmp_path,
    snapshot: dict[str, Any],
    *,
    max_body_chars: int = 4000,
) -> AgentInvocationEvidenceRecorder:
    return AgentInvocationEvidenceRecorder(
        path=tmp_path / "external_agent_invocation.json",
        agent_snapshot=snapshot,
        platform_values=_platform_values(),
        max_body_chars=max_body_chars,
    )


@pytest.mark.asyncio
async def test_sync_invocation_writes_redacted_evidence_and_logs(
    tmp_path, caplog
) -> None:
    snapshot = _sync_snapshot()
    evidence_recorder = _evidence_recorder(tmp_path, snapshot, max_body_chars=200)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Agent-Secret"] == "credential-secret"
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "answer": {"token": "response-token", "value": "ok"},
                "error": None,
                "api_key": "response-api-key",
            },
            headers={"Set-Cookie": "session=response-cookie"},
        )

    caplog.set_level(logging.INFO, logger="app.modules.agents.invocation")
    result = await AgentInvocationClient(httpx.MockTransport(handler)).invoke(
        agent_snapshot=snapshot,
        credential_payload={
            "type": "custom_header",
            "headerName": "X-Agent-Secret",
            "secret": "credential-secret",
        },
        platform_values=_platform_values(),
        evidence_recorder=evidence_recorder,
    )

    assert result.passed is True
    evidence_text = evidence_recorder.path.read_text(encoding="utf-8")
    evidence = json.loads(evidence_text)
    assert evidence["schemaVersion"] == 1
    assert evidence["agentId"] == "agt_evidence"
    assert evidence["invokeMode"] == "sync_response"
    assert evidence["evaluationId"] == "eval_001"
    assert evidence["sampleId"] == "sample_001"
    assert evidence["outcome"]["status"] == "completed"
    assert len(evidence["httpCalls"]) == 1
    call = evidence["httpCalls"][0]
    assert call["method"] == "POST"
    assert call["url"] == (
        "https://api.example.com/run?api_key=%5Bredacted%5D&trace=%5Bredacted%5D"
    )
    assert call["requestHeaders"]["X-Agent-Secret"] == "[redacted]"
    assert call["responseHeaders"]["set-cookie"] == "[redacted]"
    assert call["responseStatusCode"] == 200
    assert call["errorClass"] is None
    assert "credential-secret" not in evidence_text
    assert "body-secret" not in evidence_text
    assert "nested-password" not in evidence_text
    assert "response-token" not in evidence_text
    assert "response-api-key" not in evidence_text
    assert "response-cookie" not in evidence_text
    assert any(record.message == "agent_invocation_completed" for record in caplog.records)
    assert all("credential-secret" not in record.getMessage() for record in caplog.records)


@pytest.mark.asyncio
async def test_submit_poll_evidence_records_each_http_call(tmp_path) -> None:
    snapshot = _submit_poll_snapshot(
        base_url="https://api.browser-use.com/api/v3",
        invoke_path="/sessions",
        result_path_template="/sessions/{externalRunId}",
        platform_input_mapping={"task": "task"},
        platform_output_mapping={
            "externalRunId": "id",
            "status": "status",
            "success": "isTaskSuccessful",
            "finalAnswer": "output",
        },
        terminal_statuses=["stopped", "error"],
        success_statuses=["stopped"],
    )
    snapshot["agentId"] = "agt_poll"
    snapshot["templateId"] = "browser_use_cloud"
    evidence_recorder = _evidence_recorder(tmp_path, snapshot)
    responses = [
        httpx.Response(200, json={"id": "session_123"}),
        httpx.Response(200, json={"id": "session_123", "status": "running"}),
        httpx.Response(
            200,
            json={
                "id": "session_123",
                "status": "stopped",
                "isTaskSuccessful": True,
                "output": "done",
            },
        ),
    ]

    def handler(_request: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    result = await AgentInvocationClient(httpx.MockTransport(handler)).invoke(
        agent_snapshot=snapshot,
        credential_payload={},
        platform_values=_platform_values(),
        evidence_recorder=evidence_recorder,
    )

    evidence = json.loads(evidence_recorder.path.read_text(encoding="utf-8"))
    assert result.passed is True
    assert evidence["outcome"]["externalRunId"] == "session_123"
    assert evidence["outcome"]["status"] == "stopped"
    assert [call["method"] for call in evidence["httpCalls"]] == ["POST", "GET", "GET"]
    assert [call["responseStatusCode"] for call in evidence["httpCalls"]] == [200, 200, 200]


@pytest.mark.asyncio
async def test_invocation_evidence_records_http_error_without_raw_secret(
    tmp_path, caplog
) -> None:
    snapshot = _sync_snapshot()
    evidence_recorder = _evidence_recorder(tmp_path, snapshot)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "server failed", "token": "bad-token"})

    caplog.set_level(logging.WARNING, logger="app.modules.agents.invocation")
    with pytest.raises(AgentInvocationError, match="外部 Agent HTTP 调用失败"):
        await AgentInvocationClient(httpx.MockTransport(handler)).invoke(
            agent_snapshot=snapshot,
            credential_payload={"secret": "credential-secret"},
            platform_values=_platform_values(),
            evidence_recorder=evidence_recorder,
        )

    evidence_text = evidence_recorder.path.read_text(encoding="utf-8")
    evidence = json.loads(evidence_text)
    assert evidence["outcome"]["status"] == "failed"
    assert evidence["outcome"]["errorClass"] == "http_error"
    assert evidence["httpCalls"][0]["errorClass"] == "http_error"
    assert evidence["httpCalls"][0]["responseStatusCode"] == 500
    assert "bad-token" not in evidence_text
    assert any(record.message == "agent_invocation_failed" for record in caplog.records)


@pytest.mark.asyncio
async def test_invocation_evidence_records_invalid_json_and_response_too_large(
    tmp_path, monkeypatch
) -> None:
    invalid_snapshot = _sync_snapshot(base_url="https://invalid-json.example.com")
    invalid_recorder = _evidence_recorder(tmp_path / "invalid", invalid_snapshot)

    def invalid_json_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    with pytest.raises(AgentInvocationError, match="响应必须是 JSON 对象"):
        await AgentInvocationClient(httpx.MockTransport(invalid_json_handler)).invoke(
            agent_snapshot=invalid_snapshot,
            credential_payload={},
            platform_values=_platform_values(),
            evidence_recorder=invalid_recorder,
        )
    invalid_evidence = json.loads(invalid_recorder.path.read_text(encoding="utf-8"))
    assert invalid_evidence["outcome"]["errorClass"] == "invalid_json"
    assert invalid_evidence["httpCalls"][0]["errorClass"] == "invalid_json"

    large_snapshot = _sync_snapshot(base_url="https://large.example.com")
    large_recorder = _evidence_recorder(tmp_path / "large", large_snapshot)

    def large_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "completed", "answer": "x" * 200})

    monkeypatch.setattr(
        "app.modules.agents.invocation.settings.AGENT_HTTP_RESPONSE_MAX_BYTES",
        20,
    )
    with pytest.raises(AgentInvocationError, match="响应体过大"):
        await AgentInvocationClient(httpx.MockTransport(large_handler)).invoke(
            agent_snapshot=large_snapshot,
            credential_payload={},
            platform_values=_platform_values(),
            evidence_recorder=large_recorder,
        )
    large_evidence = json.loads(large_recorder.path.read_text(encoding="utf-8"))
    assert large_evidence["outcome"]["errorClass"] == "response_too_large"
    assert large_evidence["httpCalls"][0]["errorClass"] == "response_too_large"


@pytest.mark.asyncio
async def test_submit_poll_timeout_is_classified_in_evidence(tmp_path) -> None:
    snapshot = _submit_poll_snapshot(
        base_url="https://api.poll-timeout.example.com",
        invoke_path="/tasks",
        result_path_template="/tasks/{externalRunId}",
        platform_input_mapping={"task": "task"},
        platform_output_mapping={"externalRunId": "id", "status": "status"},
        terminal_statuses=["finished"],
        success_statuses=["finished"],
    )
    snapshot["connection"]["pollTimeoutSeconds"] = 0.001
    evidence_recorder = _evidence_recorder(tmp_path, snapshot)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(200, json={"id": "task_123"})
        return httpx.Response(200, json={"id": "task_123", "status": "running"})

    with pytest.raises(AgentInvocationError, match="轮询超时"):
        await AgentInvocationClient(httpx.MockTransport(handler)).invoke(
            agent_snapshot=snapshot,
            credential_payload={},
            platform_values={
                key: value
                for key, value in _platform_values().items()
                if key != "timeoutSeconds"
            },
            evidence_recorder=evidence_recorder,
        )

    evidence = json.loads(evidence_recorder.path.read_text(encoding="utf-8"))
    assert evidence["outcome"]["errorClass"] == "poll_timeout"
    assert evidence["outcome"]["externalRunId"] == "task_123"


def test_submit_poll_poll_timeout_uses_runtime_timeout_before_agent_default() -> None:
    timeout = _resolve_poll_timeout_seconds(
        {"pollTimeoutSeconds": 900, "requestTimeoutSeconds": 30},
        {"timeoutSeconds": 1500},
    )

    assert timeout == 1500


@pytest.mark.asyncio
async def test_submit_poll_invokes_skyvern_cloud_api_shape() -> None:
    snapshot = _submit_poll_snapshot(
        base_url="https://api.skyvern.com",
        invoke_path="/v1/run/tasks",
        result_path_template="/v1/runs/{externalRunId}",
        auth={"type": "api_key_header", "headerName": "x-api-key"},
        platform_input_mapping={
            "task": "prompt",
            "entryUrl": "url",
            "maxSteps": "max_steps",
        },
        platform_output_mapping={
            "externalRunId": "run_id",
            "status": "status",
            "finalAnswer": "output",
            "errorMessage": "failure_reason",
        },
        terminal_statuses=["completed", "failed", "timed_out", "terminated", "canceled"],
        success_statuses=["completed"],
    )

    result, requests = await _invoke_with_responses(
        snapshot=snapshot,
        credential_payload={
            "type": "api_key_header",
            "headerName": "x-api-key",
            "secret": "sk-skyvern",
        },
        submit_response={"run_id": "tsk_123"},
        poll_response={
            "run_id": "tsk_123",
            "status": "completed",
            "output": {"answer": "done"},
            "failure_reason": None,
        },
    )

    assert result.passed is True
    assert result.external_run_id == "tsk_123"
    assert result.final_answer == {"answer": "done"}
    assert str(requests[0].url) == "https://api.skyvern.com/v1/run/tasks"
    assert str(requests[1].url) == "https://api.skyvern.com/v1/runs/tsk_123"
    assert requests[0].headers["x-api-key"] == "sk-skyvern"
    assert requests[0].read() == (
        b'{"prompt":"Complete checkout","url":"https://shop.example/cart",'
        b'"max_steps":42}'
    )


@pytest.mark.asyncio
async def test_success_output_mapping_requires_true_boolean() -> None:
    snapshot = _submit_poll_snapshot(
        base_url="https://api.browser-use.com/api/v2",
        invoke_path="/tasks",
        result_path_template="/tasks/{externalRunId}/status",
        auth={
            "type": "api_key_header",
            "headerName": "X-Browser-Use-API-Key",
        },
        platform_input_mapping={
            "task": "task",
            "entryUrl": "startUrl",
            "maxSteps": "maxSteps",
        },
        platform_output_mapping={
            "externalRunId": "id",
            "status": "status",
            "success": "isSuccess",
            "finalAnswer": "output",
            "errorMessage": "output",
        },
        terminal_statuses=["finished", "failed", "stopped"],
        success_statuses=["finished"],
    )

    result, requests = await _invoke_with_responses(
        snapshot=snapshot,
        credential_payload={
            "type": "api_key_header",
            "headerName": "X-Browser-Use-API-Key",
            "secret": "sk-browser-use",
        },
        submit_response={"id": "task_123"},
        poll_response={
            "id": "task_123",
            "status": "finished",
            "output": "agent gave up",
            "isSuccess": False,
        },
    )

    assert result.passed is False
    assert result.error_message == "agent gave up"
    assert str(requests[1].url) == (
        "https://api.browser-use.com/api/v2/tasks/task_123/status"
    )
    assert requests[0].headers["X-Browser-Use-API-Key"] == "sk-browser-use"
    assert requests[0].read() == (
        b'{"task":"Complete checkout","startUrl":"https://shop.example/cart",'
        b'"maxSteps":42}'
    )


@pytest.mark.asyncio
async def test_success_output_mapping_missing_value_fails_explicitly() -> None:
    snapshot = _submit_poll_snapshot(
        base_url="https://api.browser-use.com/api/v2",
        invoke_path="/tasks",
        result_path_template="/tasks/{externalRunId}/status",
        platform_input_mapping={"task": "task"},
        platform_output_mapping={
            "externalRunId": "id",
            "status": "status",
            "success": "isSuccess",
        },
        terminal_statuses=["finished", "failed", "stopped"],
        success_statuses=["finished"],
    )

    result, _ = await _invoke_with_responses(
        snapshot=snapshot,
        credential_payload={},
        submit_response={"id": "task_123"},
        poll_response={"id": "task_123", "status": "finished"},
    )

    assert result.passed is False
    assert result.error_message == "未能从响应路径 isSuccess 解析 success。"


@pytest.mark.asyncio
async def test_goal_with_entry_url_renders_browser_use_v3_task_text() -> None:
    snapshot = _submit_poll_snapshot(
        base_url="https://api.browser-use.com/api/v3",
        invoke_path="/sessions",
        result_path_template="/sessions/{externalRunId}",
        auth={
            "type": "api_key_header",
            "headerName": "X-Browser-Use-API-Key",
        },
        task_render_mode="goal_with_entry_url",
        platform_input_mapping={
            "task": "task",
        },
        platform_output_mapping={
            "externalRunId": "id",
            "status": "status",
            "success": "isTaskSuccessful",
            "finalAnswer": "output",
            "errorMessage": "lastStepSummary",
        },
        terminal_statuses=["stopped", "timed_out", "error"],
        success_statuses=["stopped"],
    )

    result, requests = await _invoke_with_responses(
        snapshot=snapshot,
        credential_payload={
            "type": "api_key_header",
            "headerName": "X-Browser-Use-API-Key",
            "secret": "sk-browser-use",
        },
        submit_response={"id": "session_123"},
        poll_response={
            "id": "session_123",
            "status": "stopped",
            "output": {"answer": "done"},
            "isTaskSuccessful": True,
            "lastStepSummary": "Finished checkout",
        },
    )

    assert result.passed is True
    assert result.final_answer == {"answer": "done"}
    assert str(requests[1].url) == "https://api.browser-use.com/api/v3/sessions/session_123"
    assert requests[0].read() == (
        b'{"task":"Complete checkout\\n\\nStart URL: https://shop.example/cart"}'
    )


@pytest.mark.asyncio
async def test_submit_poll_cancel_uses_browser_use_v3_delete_session_without_body() -> None:
    snapshot = _submit_poll_snapshot(
        base_url="https://api.browser-use.com/api/v3",
        invoke_path="/sessions",
        result_path_template="/sessions/{externalRunId}",
        auth={
            "type": "api_key_header",
            "headerName": "X-Browser-Use-API-Key",
        },
        task_render_mode="goal_with_entry_url",
        platform_input_mapping={"task": "task"},
        platform_output_mapping={
            "externalRunId": "id",
            "status": "status",
            "success": "isTaskSuccessful",
            "finalAnswer": "output",
            "errorMessage": "lastStepSummary",
        },
        terminal_statuses=["stopped", "timed_out", "error"],
        success_statuses=["stopped"],
    )
    snapshot["connection"]["cancelPathTemplate"] = "/sessions/{externalRunId}"
    snapshot["connection"]["cancelMethod"] = "DELETE"
    snapshot["connection"]["cancelRequestBody"] = None
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(200, json={"id": "session_123"})
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json={"id": "session_123", "status": "running"})

    async def cancel_requested() -> bool:
        return True

    with pytest.raises(AgentInvocationError, match="已取消"):
        await AgentInvocationClient(httpx.MockTransport(handler)).invoke(
            agent_snapshot=snapshot,
            credential_payload={
                "type": "api_key_header",
                "headerName": "X-Browser-Use-API-Key",
                "secret": "sk-browser-use",
            },
            platform_values=_platform_values(),
            cancel_requested=cancel_requested,
        )

    assert [request.method for request in requests] == ["POST", "DELETE"]
    assert str(requests[1].url) == "https://api.browser-use.com/api/v3/sessions/session_123"
    assert requests[1].content == b""
