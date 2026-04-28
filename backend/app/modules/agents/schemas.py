"""Agent module request and response models."""

from typing import Any, Literal

from pydantic import Field

from app.shared.schemas import CamelModel


InvokeMode = Literal["sync_response", "submit_poll"]
AgentStatus = Literal["draft", "verifying", "active", "invalid", "archived"]
AuthType = Literal["none", "bearer", "api_key_header", "custom_header"]


class AgentConnection(CamelModel):
    """External Agent connection settings."""

    base_url: str
    invoke_path: str
    result_path_template: str | None = None
    request_timeout_seconds: int = Field(default=30, ge=1, le=300)
    poll_interval_seconds: float = Field(default=2, ge=0, le=60)
    poll_timeout_seconds: int = Field(default=300, ge=1, le=3600)


class AgentAuthConfig(CamelModel):
    """External Agent auth settings as submitted by the user."""

    type: AuthType
    config: dict[str, Any] = Field(default_factory=dict)


class AgentCreateRequest(CamelModel):
    """Create a runnable Agent configuration."""

    template_id: str | None = None
    name: str = Field(max_length=100)
    description: str | None = None
    invoke_mode: InvokeMode
    connection: AgentConnection
    auth: AgentAuthConfig
    platform_input_mapping: dict[str, str]
    task_render_mode: str = "goal_only"
    custom_request_body: dict[str, Any] = Field(default_factory=dict)
    request_options: dict[str, Any] = Field(default_factory=dict)
    platform_output_mapping: dict[str, str]
    terminal_statuses: list[str]
    success_statuses: list[str]


class AgentSummary(CamelModel):
    """Agent list/create summary."""

    agent_id: str
    name: str
    description: str | None = None
    invoke_mode: str
    status: str
    verified_at: str | None = None
    last_verification_passed: bool | None = None
    can_submit_evaluation: bool | None = None
    can_verify: bool | None = None
    can_archive: bool | None = None
    can_copy_create: bool | None = None
    created_at: str
    updated_at: str


class AgentAuthPublic(CamelModel):
    """Non-sensitive auth config returned by detail API."""

    type: str
    has_credential: bool
    public_config: dict[str, Any]


class AgentActions(CamelModel):
    """Actions allowed for the current Agent state."""

    can_submit_evaluation: bool
    can_verify: bool
    can_archive: bool
    can_copy_create: bool


class AgentDetail(CamelModel):
    """Full non-sensitive Agent detail."""

    agent_id: str
    template_id: str | None = None
    name: str
    description: str | None = None
    invoke_mode: str
    status: str
    connection: AgentConnection
    auth: AgentAuthPublic
    platform_input_mapping: dict[str, str]
    task_render_mode: str
    custom_request_body: dict[str, Any]
    request_options: dict[str, Any]
    platform_output_mapping: dict[str, str]
    terminal_statuses: list[str]
    success_statuses: list[str]
    verified_at: str | None = None
    last_verification: dict[str, Any] | None = None
    actions: AgentActions
    created_at: str
    updated_at: str


class AgentVerificationRequest(CamelModel):
    """Trigger a live Agent verification call."""

    timeout_seconds: int = Field(default=90, ge=1, le=600)


class AgentVerificationMessage(CamelModel):
    """Warning or error returned by Agent verification."""

    code: str
    message: str


class AgentVerificationResponse(CamelModel):
    """Agent verification result."""

    agent_id: str
    passed: bool
    status: str
    verified_at: str
    warnings: list[AgentVerificationMessage]
    errors: list[AgentVerificationMessage]


class AgentArchiveResponse(CamelModel):
    """Archive action response."""

    agent_id: str
    status: str
    updated_at: str


class AgentTemplate(CamelModel):
    """Agent registration template."""

    template_id: str
    name: str
    description: str
    recommended: bool
    sort_order: int
    level: str
    tags: list[str]
    default_config: dict[str, Any]
