"""Agent response and runtime snapshot mapping helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.agent import Agent
from app.modules.agents.domain.policies import actions_for_status
from app.modules.agents.schemas import AgentDetail, AgentSummary


def to_zulu(value: datetime | None) -> str | None:
    """Format datetimes for public API responses."""
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def to_summary(agent: Agent, *, include_actions: bool) -> AgentSummary:
    """Map an Agent ORM row to its public summary schema."""
    payload = {
        "agentId": agent.public_id,
        "name": agent.name,
        "description": agent.description,
        "invokeMode": agent.invoke_mode,
        "maxConcurrency": agent.max_concurrency,
        "status": agent.status,
        "verifiedAt": to_zulu(agent.verified_at),
        "lastVerificationPassed": agent.last_verification_passed,
        "createdAt": to_zulu(agent.created_at),
        "updatedAt": to_zulu(agent.updated_at),
    }
    if include_actions:
        payload.update(actions_for_status(agent.status))
    return AgentSummary.model_validate(payload)


def to_detail(agent: Agent) -> AgentDetail:
    """Map an Agent ORM row to its non-sensitive detail schema."""
    return AgentDetail.model_validate(
        {
            "agentId": agent.public_id,
            "templateId": agent.template_id,
            "name": agent.name,
            "description": agent.description,
            "invokeMode": agent.invoke_mode,
            "maxConcurrency": agent.max_concurrency,
            "status": agent.status,
            "connection": agent.connection,
            "auth": {
                "type": agent.auth_type,
                "hasCredential": agent.credential_ref is not None,
                "publicConfig": agent.auth_public_config,
            },
            "platformInputMapping": agent.platform_input_mapping,
            "taskRenderMode": agent.task_render_mode,
            "customRequestBody": agent.custom_request_body,
            "requestOptions": agent.request_options,
            "platformOutputMapping": agent.platform_output_mapping,
            "terminalStatuses": agent.terminal_statuses,
            "successStatuses": agent.success_statuses,
            "verifiedAt": to_zulu(agent.verified_at),
            "lastVerification": agent.last_verification,
            "actions": actions_for_status(agent.status),
            "createdAt": to_zulu(agent.created_at),
            "updatedAt": to_zulu(agent.updated_at),
        }
    )


def runtime_snapshot(agent: Agent) -> dict[str, object]:
    """Freeze an Agent configuration for worker/runtime execution."""
    return {
        "agentId": agent.public_id,
        "templateId": agent.template_id,
        "name": agent.name,
        "description": agent.description,
        "invokeMode": agent.invoke_mode,
        "maxConcurrency": agent.max_concurrency,
        "connection": agent.connection,
        "auth": {
            "type": agent.auth_type,
            **agent.auth_public_config,
            "credentialRef": agent.credential_ref,
        },
        "platformInputMapping": agent.platform_input_mapping,
        "taskRenderMode": agent.task_render_mode,
        "customRequestBody": agent.custom_request_body,
        "requestOptions": agent.request_options,
        "platformOutputMapping": agent.platform_output_mapping,
        "terminalStatuses": agent.terminal_statuses,
        "successStatuses": agent.success_statuses,
    }
