from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.agents.schemas import AgentCreateRequest


def _minimal_agent_payload() -> dict[str, object]:
    return {
        "templateId": "http_submit_poll_basic",
        "name": "Schema Agent",
        "description": "schema validation",
        "invokeMode": "sync_response",
        "maxConcurrency": 4,
        "connection": {
            "baseUrl": "https://agent.example.com",
            "invokePath": "/run",
            "requestTimeoutSeconds": 30,
        },
        "auth": {"type": "none", "config": {}},
        "platformInputMapping": {"task": "prompt"},
        "taskRenderMode": "goal_only",
        "customRequestBody": {},
        "requestOptions": {},
        "platformOutputMapping": {"finalAnswer": "answer"},
        "terminalStatuses": ["completed", "failed"],
        "successStatuses": ["completed"],
    }


def test_agent_create_request_requires_max_concurrency() -> None:
    payload = _minimal_agent_payload()
    del payload["maxConcurrency"]

    with pytest.raises(ValidationError) as exc_info:
        AgentCreateRequest.model_validate(payload)

    assert exc_info.value.errors()[0]["loc"] == ("maxConcurrency",)


def test_agent_create_request_rejects_max_concurrency_outside_range() -> None:
    payload = _minimal_agent_payload()
    payload["maxConcurrency"] = 101

    with pytest.raises(ValidationError) as exc_info:
        AgentCreateRequest.model_validate(payload)

    assert exc_info.value.errors()[0]["loc"] == ("maxConcurrency",)


def test_agent_create_request_rejects_unsupported_cancel_method() -> None:
    payload = _minimal_agent_payload()
    connection = payload["connection"]
    assert isinstance(connection, dict)
    connection["cancelPathTemplate"] = "/runs/{externalRunId}/cancel"
    connection["cancelMethod"] = "GET"

    with pytest.raises(ValidationError) as exc_info:
        AgentCreateRequest.model_validate(payload)

    assert exc_info.value.errors()[0]["loc"] == ("connection", "cancelMethod")
