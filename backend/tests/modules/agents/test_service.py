from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.modules.agents.schemas import AgentCreateRequest
from app.modules.agents.service import AgentService
from app.platform.errors import ValidationDomainError


def build_agent_payload(**overrides) -> AgentCreateRequest:
    payload = {
        "templateId": "http_submit_poll_basic",
        "name": "Demo Agent",
        "description": "demo",
        "invokeMode": "submit_poll",
        "connection": {
            "baseUrl": "https://api.agent.example.com",
            "invokePath": "/runs",
            "resultPathTemplate": "/runs/{externalRunId}",
            "requestTimeoutSeconds": 30,
            "pollIntervalSeconds": 1,
            "pollTimeoutSeconds": 30,
        },
        "auth": {"type": "api_key_header", "config": {"headerName": "x-api-key", "secret": "sk-demo"}},
        "platformInputMapping": {"task": "prompt"},
        "taskRenderMode": "goal_only",
        "customRequestBody": {},
        "requestOptions": {},
        "platformOutputMapping": {"externalRunId": "id", "status": "status", "finalAnswer": "answer"},
        "terminalStatuses": ["completed", "failed"],
        "successStatuses": ["completed"],
    }
    payload.update(overrides)
    return AgentCreateRequest.model_validate(payload)


class AgentRepositoryStub:
    async def create(self, agent):
        return agent


class MemoryCredentialStore:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    def store(self, payload: dict[str, object]) -> str:
        self.payloads.append(payload)
        return "secret_demo"

    def load(self, credential_ref: str) -> dict[str, object]:
        return self.payloads[0]

    def delete(self, credential_ref: str) -> None:
        pass


@pytest.mark.asyncio
async def test_create_agent_rejects_custom_body_mapping_conflict() -> None:
    service = AgentService(AgentRepositoryStub(), credential_store=MemoryCredentialStore())
    payload = build_agent_payload(customRequestBody={"prompt": "fixed"})

    with pytest.raises(ValidationDomainError) as exc:
        await service.create_agent(payload, SimpleNamespace(id=1))

    assert exc.value.code == 40002
    assert "字段冲突" in exc.value.message


@pytest.mark.asyncio
async def test_create_agent_stores_secret_and_returns_draft_summary() -> None:
    credential_store = MemoryCredentialStore()
    service = AgentService(AgentRepositoryStub(), credential_store=credential_store)

    response = await service.create_agent(build_agent_payload(), SimpleNamespace(id=1))

    assert response.agent_id.startswith("agt_")
    assert response.status == "draft"
    assert credential_store.payloads == [{"type": "api_key_header", "headerName": "x-api-key", "secret": "sk-demo"}]
