"""Agent module service layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from app.models.agent import Agent
from app.modules.agents.application.ids import generate_agent_id
from app.modules.agents.application.mappers import (
    runtime_snapshot,
    to_detail,
    to_summary,
    to_zulu,
)
from app.modules.agents.domain.policies import (
    actions_for_status,
    invalid_agent,
    split_auth_config,
    validate_create_payload,
)
from app.modules.agents.invocation import AgentInvocationClient
from app.modules.agents.repository import AgentRepository
from app.modules.agents.schemas import (
    AgentArchiveResponse,
    AgentCreateRequest,
    AgentDetail,
    AgentSummary,
    AgentVerificationRequest,
    AgentVerificationResponse,
)
from app.modules.agents.templates import list_agent_templates
from app.platform.credentials import CredentialStore
from app.platform.errors import ConflictError, ForbiddenError, NotFoundError
from app.platform.i18n import translate
from app.platform.storage import default_credential_store


AGENT_VERIFICATION_ENTRY_URL = "https://www.iana.org/domains/reserved"
AGENT_VERIFICATION_MAX_STEPS = 5
AGENT_VERIFICATION_TASK = (
    "Open the provided URL and confirm the main page heading is "
    "'IANA-managed Reserved Domains'. Return the heading text when complete."
)


class AgentService:
    """Coordinate Agent registration, verification and archival."""

    def __init__(
        self,
        repository: AgentRepository,
        credential_store: CredentialStore | None = None,
        invocation_client: AgentInvocationClient | None = None,
    ) -> None:
        self.repository = repository
        self.credential_store = credential_store or default_credential_store()
        self.invocation_client = invocation_client or AgentInvocationClient()

    async def list_templates(self):
        """Return built-in templates."""
        return list_agent_templates()

    async def create_agent(
        self, payload: AgentCreateRequest, current_user
    ) -> AgentSummary:
        """Create a draft Agent and persist any submitted credential separately."""
        validate_create_payload(payload)
        now = datetime.now(timezone.utc)
        public_config, credential_payload = split_auth_config(payload)
        credential_ref = (
            self.credential_store.store(credential_payload)
            if credential_payload
            else None
        )
        agent = Agent(
            public_id=generate_agent_id(),
            user_id=current_user.id,
            template_id=payload.template_id,
            name=payload.name.strip(),
            description=(payload.description or "").strip() or None,
            invoke_mode=payload.invoke_mode,
            status="draft",
            connection=payload.connection.model_dump(by_alias=True),
            auth_type=payload.auth.type,
            auth_public_config=public_config,
            credential_ref=credential_ref,
            platform_input_mapping=dict(payload.platform_input_mapping),
            task_render_mode=payload.task_render_mode,
            custom_request_body=dict(payload.custom_request_body),
            request_options=dict(payload.request_options),
            platform_output_mapping=dict(payload.platform_output_mapping),
            terminal_statuses=list(payload.terminal_statuses),
            success_statuses=list(payload.success_statuses),
            verified_at=None,
            last_verification_passed=None,
            last_verification=None,
            created_at=now,
            updated_at=now,
        )
        try:
            agent = await self.repository.create(agent)
        except Exception:
            if credential_ref is not None:
                self.credential_store.delete(credential_ref)
            raise
        return to_summary(agent, include_actions=False)

    async def list_agents(
        self, current_user, *, include_archived: bool = False, status: str | None = None
    ) -> list[AgentSummary]:
        """List Agents for the current user."""
        agents = await self.repository.list_for_user(
            current_user.id, include_archived=include_archived, status=status
        )
        return [to_summary(agent, include_actions=True) for agent in agents]

    async def get_agent_detail(self, agent_id: str, current_user) -> AgentDetail:
        """Return non-sensitive Agent detail."""
        agent = await self._get_owned_agent(agent_id, current_user)
        return to_detail(agent)

    async def verify_agent(
        self, agent_id: str, payload: AgentVerificationRequest, current_user
    ) -> AgentVerificationResponse:
        """Run a lightweight live verification against the external Agent."""
        agent = await self._get_owned_agent(agent_id, current_user)
        if agent.status == "archived":
            raise ConflictError(
                "已归档 Agent 不能验证。",
                code=40901,
                message_key="agents.errors.archived_verify",
            )
        if agent.status == "verifying":
            raise ConflictError(
                "Agent 正在验证中，请稍后再试。",
                code=40901,
                message_key="agents.errors.verifying",
            )

        now = datetime.now(timezone.utc)
        agent.status = "verifying"
        agent.updated_at = now
        await self.repository.commit()
        await self.repository.refresh(agent)

        warnings: list[dict[str, str]] = []
        errors: list[dict[str, str]] = []
        passed = False
        try:
            credential_payload = (
                self.credential_store.load(agent.credential_ref)
                if agent.credential_ref
                else {}
            )
            result = await self.invocation_client.invoke(
                agent_snapshot=runtime_snapshot(agent),
                credential_payload=credential_payload,
                platform_values={
                    "task": AGENT_VERIFICATION_TASK,
                    "entryUrl": AGENT_VERIFICATION_ENTRY_URL,
                    "timeoutSeconds": payload.timeout_seconds,
                    "sampleId": "verification",
                    "evaluationId": "verification",
                    "maxSteps": AGENT_VERIFICATION_MAX_STEPS,
                },
            )
            passed = result.passed
            if not passed:
                errors.append(
                    {
                        "code": "AGENT_STATUS_NOT_SUCCESS",
                        "message": result.error_message
                        or translate("agents.errors.status_not_success"),
                    }
                )
        except Exception as exc:
            errors.append({"code": exc.__class__.__name__.upper(), "message": str(exc)})

        verified_at = datetime.now(timezone.utc)
        agent.status = "active" if passed else "invalid"
        agent.verified_at = verified_at
        agent.last_verification_passed = passed
        agent.last_verification = {
            "passed": passed,
            "warnings": warnings,
            "errors": errors,
        }
        agent.updated_at = verified_at
        await self.repository.commit()
        await self.repository.refresh(agent)

        return AgentVerificationResponse.model_validate(
            {
                "agentId": agent.public_id,
                "passed": passed,
                "status": agent.status,
                "verifiedAt": to_zulu(agent.verified_at),
                "warnings": warnings,
                "errors": errors,
            }
        )

    async def archive_agent(self, agent_id: str, current_user) -> AgentArchiveResponse:
        """Archive an Agent."""
        agent = await self._get_owned_agent(agent_id, current_user)
        if agent.status == "archived":
            raise ConflictError(
                "已归档 Agent 不能重复归档。",
                code=40901,
                message_key="agents.errors.archived_again",
            )
        now = datetime.now(timezone.utc)
        agent.status = "archived"
        agent.updated_at = now
        await self.repository.commit()
        await self.repository.refresh(agent)
        archived_updated_at = to_zulu(cast(datetime, agent.updated_at))
        assert archived_updated_at is not None
        return AgentArchiveResponse(
            agent_id=agent.public_id,
            status=agent.status,
            updated_at=archived_updated_at,
        )

    async def _get_owned_agent(self, agent_id: str, current_user) -> Agent:
        agent = await self.repository.get_by_public_id(agent_id)
        if agent is None:
            raise NotFoundError("Agent 不存在。", message_key="agents.errors.not_found")
        if agent.user_id != current_user.id:
            raise ForbiddenError(
                "无权访问该 Agent。", message_key="agents.errors.forbidden"
            )
        return agent
