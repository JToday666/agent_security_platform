from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.modules.agents.invocation import AgentInvocationClient


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
