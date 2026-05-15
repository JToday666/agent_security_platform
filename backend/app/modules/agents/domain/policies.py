"""Agent validation and state policy helpers."""

from __future__ import annotations

from app.modules.agents.schemas import AgentCreateRequest
from app.modules.agents.security import AgentUrlSecurityError, validate_agent_base_url
from app.platform.errors import ValidationDomainError


def invalid_agent(
    message: str, *, message_key: str | None = None
) -> ValidationDomainError:
    """Build a stable Agent validation error."""
    return ValidationDomainError(
        message, http_status=400, code=40002, message_key=message_key
    )


def actions_for_status(status: str) -> dict[str, bool]:
    """Derive frontend actions from Agent status."""
    return {
        "canSubmitEvaluation": status == "active",
        "canVerify": status in {"draft", "active", "invalid"},
        "canArchive": status in {"draft", "verifying", "active", "invalid"},
        "canCopyCreate": status
        in {"draft", "verifying", "active", "invalid", "archived"},
    }


def validate_create_payload(payload: AgentCreateRequest) -> None:
    """Validate a submitted Agent configuration before persistence."""
    name = payload.name.strip()
    if not name:
        raise invalid_agent(
            "Agent 名称不能为空。", message_key="agents.errors.name_required"
        )
    try:
        validate_agent_base_url(payload.connection.base_url)
    except AgentUrlSecurityError as exc:
        raise invalid_agent(str(exc)) from exc
    if (
        "task" not in payload.platform_input_mapping
        or not payload.platform_input_mapping["task"]
    ):
        raise invalid_agent("platformInputMapping.task 必填。")
    for field in payload.platform_input_mapping.values():
        if not _top_level_field(field):
            raise invalid_agent("platformInputMapping 的值必须是顶层字段名。")
    conflict = set(payload.custom_request_body.keys()).intersection(
        payload.platform_input_mapping.values()
    )
    if conflict:
        raise invalid_agent(
            f"customRequestBody 中的字段 {sorted(conflict)[0]} 与平台输入映射字段冲突。"
        )
    if payload.invoke_mode == "submit_poll":
        if not payload.connection.result_path_template:
            raise invalid_agent("submit_poll 模式下 resultPathTemplate 为必填字段。")
        for key in ("externalRunId", "status"):
            if key not in payload.platform_output_mapping:
                raise invalid_agent(
                    f"submit_poll 模式下 platformOutputMapping.{key} 为必填字段。"
                )
    if not set(payload.success_statuses).issubset(set(payload.terminal_statuses)):
        raise invalid_agent("successStatuses 必须是 terminalStatuses 的子集。")
    _validate_auth(payload)


def split_auth_config(
    payload: AgentCreateRequest,
) -> tuple[dict[str, object], dict[str, object] | None]:
    """Split public auth config from sensitive credential payload."""
    config = dict(payload.auth.config)
    if payload.auth.type == "none":
        return {}, None
    if payload.auth.type == "bearer":
        return {"hasToken": True}, {"type": "bearer", "token": config["token"]}
    return (
        {"headerName": config["headerName"], "hasSecret": True},
        {
            "type": payload.auth.type,
            "headerName": config["headerName"],
            "secret": config["secret"],
        },
    )


def _top_level_field(value: str) -> bool:
    return bool(value and "." not in value and "[" not in value and "]" not in value)


def _validate_auth(payload: AgentCreateRequest) -> None:
    config = payload.auth.config
    if payload.auth.type == "bearer" and not config.get("token"):
        raise invalid_agent("bearer 鉴权必须填写 token。")
    if payload.auth.type in {"api_key_header", "custom_header"}:
        if not config.get("headerName") or not config.get("secret"):
            raise invalid_agent("header 鉴权必须填写 headerName 和 secret。")
