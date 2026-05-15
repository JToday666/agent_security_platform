from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.modules.agents.schemas import AgentCreateRequest, AgentVerificationRequest
from app.modules.agents.service import AgentService
from app.modules.agents.templates import list_agent_templates
from app.platform.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationDomainError,
)
from app.platform.i18n import set_current_locale


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
        "auth": {
            "type": "api_key_header",
            "config": {"headerName": "x-api-key", "secret": "sk-demo"},
        },
        "platformInputMapping": {"task": "prompt"},
        "taskRenderMode": "goal_only",
        "customRequestBody": {},
        "requestOptions": {},
        "platformOutputMapping": {
            "externalRunId": "id",
            "status": "status",
            "finalAnswer": "answer",
        },
        "terminalStatuses": ["completed", "failed"],
        "successStatuses": ["completed"],
    }
    payload.update(overrides)
    return AgentCreateRequest.model_validate(payload)


def test_agent_templates_are_localized_from_current_locale() -> None:
    token = set_current_locale("en-US")
    try:
        template = list_agent_templates()[0]
    finally:
        token.reset()

    assert template.name == "Submit + Poll Agent"
    assert (
        template.description
        == "For Agents that submit a task first, then poll the result by run ID."
    )
    assert template.tags == ["Recommended", "Async", "Polling"]


class AgentRepositoryStub:
    async def create(self, agent):
        return agent


class AgentLookupRepositoryStub:
    def __init__(self, agent) -> None:
        self.agent = agent

    async def get_by_public_id(self, agent_id: str):
        return self.agent

    async def commit(self) -> None:
        pass

    async def refresh(self, agent) -> None:
        pass


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


class AgentInvocationStub:
    async def invoke(self, **kwargs):
        return SimpleNamespace(passed=False, error_message=None)


def build_agent_row(**overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "public_id": "agt_1",
        "template_id": "http_submit_poll_basic",
        "name": "Demo Agent",
        "description": "demo",
        "user_id": 1,
        "invoke_mode": "submit_poll",
        "status": "active",
        "connection": {
            "baseUrl": "https://api.agent.example.com",
            "invokePath": "/runs",
            "resultPathTemplate": "/runs/{externalRunId}",
        },
        "auth_type": "none",
        "auth_public_config": {},
        "credential_ref": None,
        "platform_input_mapping": {"task": "prompt"},
        "task_render_mode": "goal_only",
        "custom_request_body": {},
        "request_options": {},
        "platform_output_mapping": {
            "externalRunId": "id",
            "status": "status",
            "finalAnswer": "answer",
        },
        "terminal_statuses": ["completed", "failed"],
        "success_statuses": ["completed"],
        "verified_at": None,
        "last_verification_passed": None,
        "last_verification": None,
        "created_at": now,
        "updated_at": now,
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


@pytest.mark.asyncio
async def test_create_agent_rejects_custom_body_mapping_conflict() -> None:
    service = AgentService(
        AgentRepositoryStub(), credential_store=MemoryCredentialStore()
    )
    payload = build_agent_payload(customRequestBody={"prompt": "fixed"})

    with pytest.raises(ValidationDomainError) as exc:
        await service.create_agent(payload, SimpleNamespace(id=1))

    assert exc.value.code == 40002
    assert "字段冲突" in exc.value.message


@pytest.mark.asyncio
async def test_create_agent_blank_name_carries_message_key() -> None:
    service = AgentService(
        AgentRepositoryStub(), credential_store=MemoryCredentialStore()
    )

    with pytest.raises(ValidationDomainError) as exc:
        await service.create_agent(build_agent_payload(name=" "), SimpleNamespace(id=1))

    assert exc.value.message_key == "agents.errors.name_required"


@pytest.mark.asyncio
async def test_create_agent_stores_secret_and_returns_draft_summary() -> None:
    credential_store = MemoryCredentialStore()
    service = AgentService(AgentRepositoryStub(), credential_store=credential_store)

    response = await service.create_agent(build_agent_payload(), SimpleNamespace(id=1))

    assert response.agent_id.startswith("agt_")
    assert response.status == "draft"
    assert credential_store.payloads == [
        {"type": "api_key_header", "headerName": "x-api-key", "secret": "sk-demo"}
    ]


@pytest.mark.asyncio
async def test_verify_agent_archived_conflict_carries_message_key() -> None:
    service = AgentService(
        AgentLookupRepositoryStub(
            SimpleNamespace(public_id="agt_1", user_id=1, status="archived")
        )
    )

    with pytest.raises(ConflictError) as exc:
        await service.verify_agent(
            "agt_1", AgentVerificationRequest(), SimpleNamespace(id=1)
        )

    assert exc.value.message_key == "agents.errors.archived_verify"


@pytest.mark.asyncio
async def test_verify_agent_verifying_conflict_carries_message_key() -> None:
    service = AgentService(
        AgentLookupRepositoryStub(
            SimpleNamespace(public_id="agt_1", user_id=1, status="verifying")
        )
    )

    with pytest.raises(ConflictError) as exc:
        await service.verify_agent(
            "agt_1", AgentVerificationRequest(), SimpleNamespace(id=1)
        )

    assert exc.value.message_key == "agents.errors.verifying"


@pytest.mark.asyncio
async def test_archive_agent_archived_conflict_carries_message_key() -> None:
    service = AgentService(
        AgentLookupRepositoryStub(
            SimpleNamespace(public_id="agt_1", user_id=1, status="archived")
        )
    )

    with pytest.raises(ConflictError) as exc:
        await service.archive_agent("agt_1", SimpleNamespace(id=1))

    assert exc.value.message_key == "agents.errors.archived_again"


@pytest.mark.asyncio
async def test_get_agent_detail_not_found_and_forbidden_carry_message_keys() -> None:
    service = AgentService(AgentLookupRepositoryStub(None))
    with pytest.raises(NotFoundError) as not_found:
        await service.get_agent_detail("agt_missing", SimpleNamespace(id=1))
    assert not_found.value.message_key == "agents.errors.not_found"

    service = AgentService(
        AgentLookupRepositoryStub(
            SimpleNamespace(public_id="agt_1", user_id=2, status="draft")
        )
    )
    with pytest.raises(ForbiddenError) as forbidden:
        await service.get_agent_detail("agt_1", SimpleNamespace(id=1))
    assert forbidden.value.message_key == "agents.errors.forbidden"


@pytest.mark.asyncio
async def test_verify_agent_default_failure_message_uses_current_locale() -> None:
    service = AgentService(
        AgentLookupRepositoryStub(build_agent_row()),
        credential_store=MemoryCredentialStore(),
        invocation_client=AgentInvocationStub(),
    )
    token = set_current_locale("en-US")
    try:
        response = await service.verify_agent(
            "agt_1", AgentVerificationRequest(), SimpleNamespace(id=1)
        )
    finally:
        token.reset()

    assert response.passed is False
    assert (
        response.errors[0].message
        == "The external Agent did not return a successful status."
    )
