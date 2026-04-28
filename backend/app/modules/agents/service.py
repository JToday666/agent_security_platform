"""Agent module service layer."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.agent import Agent
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
from app.modules.agents.security import AgentUrlSecurityError, validate_agent_base_url
from app.modules.agents.templates import list_agent_templates
from app.shared.config import settings
from app.shared.credentials import CredentialStore, FileCredentialStore
from app.shared.errors import ConflictError, ForbiddenError, NotFoundError, ValidationDomainError


def invalid_agent(message: str) -> ValidationDomainError:
    """Build a stable Agent validation error."""
    return ValidationDomainError(message, http_status=400, code=40002)


def to_zulu(value: datetime | None) -> str | None:
    """Format datetimes for public API responses."""
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def generate_agent_id() -> str:
    """Generate a public Agent identifier."""
    return f"agt_{uuid4().hex[:12]}"


def actions_for_status(status: str) -> dict[str, bool]:
    """Derive frontend actions from Agent status."""
    return {
        "canSubmitEvaluation": status == "active",
        "canVerify": status in {"draft", "active", "invalid"},
        "canArchive": status in {"draft", "verifying", "active", "invalid"},
        "canCopyCreate": status in {"draft", "verifying", "active", "invalid", "archived"},
    }


def _top_level_field(value: str) -> bool:
    return bool(value and "." not in value and "[" not in value and "]" not in value)


class AgentService:
    """Coordinate Agent registration, verification and archival."""

    def __init__(
        self,
        repository: AgentRepository,
        credential_store: CredentialStore | None = None,
        invocation_client: AgentInvocationClient | None = None,
    ) -> None:
        self.repository = repository
        self.credential_store = credential_store or FileCredentialStore(settings.credential_storage_dir, settings.SECRET_KEY)
        self.invocation_client = invocation_client or AgentInvocationClient()

    async def list_templates(self):
        """Return built-in templates."""
        return list_agent_templates()

    async def create_agent(self, payload: AgentCreateRequest, current_user) -> AgentSummary:
        """Create a draft Agent and persist any submitted credential separately."""
        self._validate_create_payload(payload)
        now = datetime.now(timezone.utc)
        public_config, credential_payload = self._split_auth_config(payload)
        credential_ref = self.credential_store.store(credential_payload) if credential_payload else None
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
        return self._summary(agent, include_actions=False)

    async def list_agents(self, current_user, *, include_archived: bool = False, status: str | None = None) -> list[AgentSummary]:
        """List Agents for the current user."""
        agents = await self.repository.list_for_user(current_user.id, include_archived=include_archived, status=status)
        return [self._summary(agent, include_actions=True) for agent in agents]

    async def get_agent_detail(self, agent_id: str, current_user) -> AgentDetail:
        """Return non-sensitive Agent detail."""
        agent = await self._get_owned_agent(agent_id, current_user)
        return self._detail(agent)

    async def verify_agent(self, agent_id: str, payload: AgentVerificationRequest, current_user) -> AgentVerificationResponse:
        """Run a lightweight live verification against the external Agent."""
        agent = await self._get_owned_agent(agent_id, current_user)
        if agent.status == "archived":
            raise ConflictError("已归档 Agent 不能验证。", code=40901)
        if agent.status == "verifying":
            raise ConflictError("Agent 正在验证中，请稍后再试。", code=40901)

        now = datetime.now(timezone.utc)
        agent.status = "verifying"
        agent.updated_at = now
        await self.repository.commit()
        await self.repository.refresh(agent)

        warnings: list[dict[str, str]] = []
        errors: list[dict[str, str]] = []
        passed = False
        try:
            credential_payload = self.credential_store.load(agent.credential_ref) if agent.credential_ref else {}
            result = await self.invocation_client.invoke(
                agent_snapshot=self._runtime_snapshot(agent),
                credential_payload=credential_payload,
                platform_values={
                    "task": "Agent verification probe",
                    "entryUrl": "https://example.com/__agent_verify__",
                    "timeoutSeconds": payload.timeout_seconds,
                    "sampleId": "verification",
                    "evaluationId": "verification",
                    "maxSteps": 1,
                },
            )
            passed = result.passed
            if not passed:
                errors.append({"code": "AGENT_STATUS_NOT_SUCCESS", "message": result.error_message or "外部 Agent 未返回成功状态。"})
        except Exception as exc:
            errors.append({"code": exc.__class__.__name__.upper(), "message": str(exc)})

        verified_at = datetime.now(timezone.utc)
        agent.status = "active" if passed else "invalid"
        agent.verified_at = verified_at
        agent.last_verification_passed = passed
        agent.last_verification = {"passed": passed, "warnings": warnings, "errors": errors}
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
            raise ConflictError("已归档 Agent 不能重复归档。", code=40901)
        now = datetime.now(timezone.utc)
        agent.status = "archived"
        agent.updated_at = now
        await self.repository.commit()
        await self.repository.refresh(agent)
        return AgentArchiveResponse(agent_id=agent.public_id, status=agent.status, updated_at=to_zulu(agent.updated_at))

    async def _get_owned_agent(self, agent_id: str, current_user) -> Agent:
        agent = await self.repository.get_by_public_id(agent_id)
        if agent is None:
            raise NotFoundError("Agent 不存在。")
        if agent.user_id != current_user.id:
            raise ForbiddenError("无权访问该 Agent。")
        return agent

    def _validate_create_payload(self, payload: AgentCreateRequest) -> None:
        name = payload.name.strip()
        if not name:
            raise invalid_agent("Agent 名称不能为空。")
        try:
            validate_agent_base_url(payload.connection.base_url)
        except AgentUrlSecurityError as exc:
            raise invalid_agent(str(exc)) from exc
        if "task" not in payload.platform_input_mapping or not payload.platform_input_mapping["task"]:
            raise invalid_agent("platformInputMapping.task 必填。")
        for field in payload.platform_input_mapping.values():
            if not _top_level_field(field):
                raise invalid_agent("platformInputMapping 的值必须是顶层字段名。")
        conflict = set(payload.custom_request_body.keys()).intersection(payload.platform_input_mapping.values())
        if conflict:
            raise invalid_agent(f"customRequestBody 中的字段 {sorted(conflict)[0]} 与平台输入映射字段冲突。")
        if payload.invoke_mode == "submit_poll":
            if not payload.connection.result_path_template:
                raise invalid_agent("submit_poll 模式下 resultPathTemplate 为必填字段。")
            for key in ("externalRunId", "status"):
                if key not in payload.platform_output_mapping:
                    raise invalid_agent(f"submit_poll 模式下 platformOutputMapping.{key} 为必填字段。")
        if not set(payload.success_statuses).issubset(set(payload.terminal_statuses)):
            raise invalid_agent("successStatuses 必须是 terminalStatuses 的子集。")
        self._validate_auth(payload)

    def _validate_auth(self, payload: AgentCreateRequest) -> None:
        config = payload.auth.config
        if payload.auth.type == "bearer" and not config.get("token"):
            raise invalid_agent("bearer 鉴权必须填写 token。")
        if payload.auth.type in {"api_key_header", "custom_header"}:
            if not config.get("headerName") or not config.get("secret"):
                raise invalid_agent("header 鉴权必须填写 headerName 和 secret。")

    def _split_auth_config(self, payload: AgentCreateRequest) -> tuple[dict[str, object], dict[str, object] | None]:
        config = dict(payload.auth.config)
        if payload.auth.type == "none":
            return {}, None
        if payload.auth.type == "bearer":
            return {"hasToken": True}, {"type": "bearer", "token": config["token"]}
        return (
            {"headerName": config["headerName"], "hasSecret": True},
            {"type": payload.auth.type, "headerName": config["headerName"], "secret": config["secret"]},
        )

    def _summary(self, agent: Agent, *, include_actions: bool) -> AgentSummary:
        payload = {
            "agentId": agent.public_id,
            "name": agent.name,
            "description": agent.description,
            "invokeMode": agent.invoke_mode,
            "status": agent.status,
            "verifiedAt": to_zulu(agent.verified_at),
            "lastVerificationPassed": agent.last_verification_passed,
            "createdAt": to_zulu(agent.created_at),
            "updatedAt": to_zulu(agent.updated_at),
        }
        if include_actions:
            payload.update(actions_for_status(agent.status))
        return AgentSummary.model_validate(payload)

    def _detail(self, agent: Agent) -> AgentDetail:
        return AgentDetail.model_validate(
            {
                "agentId": agent.public_id,
                "templateId": agent.template_id,
                "name": agent.name,
                "description": agent.description,
                "invokeMode": agent.invoke_mode,
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

    def _runtime_snapshot(self, agent: Agent) -> dict[str, object]:
        return {
            "agentId": agent.public_id,
            "templateId": agent.template_id,
            "name": agent.name,
            "description": agent.description,
            "invokeMode": agent.invoke_mode,
            "connection": agent.connection,
            "auth": {"type": agent.auth_type, **agent.auth_public_config, "credentialRef": agent.credential_ref},
            "platformInputMapping": agent.platform_input_mapping,
            "taskRenderMode": agent.task_render_mode,
            "customRequestBody": agent.custom_request_body,
            "requestOptions": agent.request_options,
            "platformOutputMapping": agent.platform_output_mapping,
            "terminalStatuses": agent.terminal_statuses,
            "successStatuses": agent.success_statuses,
        }
