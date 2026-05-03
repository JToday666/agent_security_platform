"""HTTP invocation client for registered external Agents."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx

from app.modules.agents.security import validate_agent_base_url
from app.platform.config import settings


class AgentInvocationError(RuntimeError):
    """Raised when an external Agent call cannot complete."""


@dataclass(slots=True)
class AgentInvocationResult:
    """Normalized external Agent lifecycle result."""

    passed: bool
    status: str | None
    external_run_id: str | None
    final_answer: Any
    error_message: str | None
    raw_response: dict[str, Any]


def read_json_path(payload: Any, path: str | None) -> Any:
    """Read a dotted path from a JSON-like object."""
    if not path:
        return None
    current = payload
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        return None
    return current


def build_agent_request_body(
    *,
    custom_request_body: dict[str, Any],
    platform_input_mapping: dict[str, str],
    platform_values: dict[str, Any],
) -> dict[str, Any]:
    """Merge fixed request fields with mapped platform values."""
    body = dict(custom_request_body or {})
    mapped_fields = {field for field in platform_input_mapping.values() if field}
    conflict = mapped_fields.intersection(body.keys())
    if conflict:
        raise ValueError(f"customRequestBody 字段冲突: {sorted(conflict)[0]}")
    for platform_key, target_field in platform_input_mapping.items():
        if not target_field or platform_key not in platform_values:
            continue
        value = platform_values[platform_key]
        if value is not None:
            body[target_field] = value
    return body


def _join_url(base_url: str, path: str) -> str:
    parsed_path = httpx.URL(path)
    if parsed_path.scheme and parsed_path.host:
        return validate_agent_base_url(path)
    base = validate_agent_base_url(base_url)
    return urljoin(f"{base}/", path.lstrip("/"))


def _auth_headers(auth: dict[str, Any], credential_payload: dict[str, Any]) -> dict[str, str]:
    auth_type = str(auth.get("type") or credential_payload.get("type") or "none")
    if auth_type == "none":
        return {}
    if auth_type == "bearer":
        token = credential_payload.get("token")
        return {} if not token else {"Authorization": f"Bearer {token}"}
    if auth_type in {"api_key_header", "custom_header"}:
        header_name = credential_payload.get("headerName") or auth.get("headerName")
        secret = credential_payload.get("secret")
        return {} if not header_name or not secret else {str(header_name): str(secret)}
    return {}


class AgentInvocationClient:
    """Call external Agent HTTP endpoints and normalize their responses."""

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.transport = transport

    async def invoke(
        self,
        *,
        agent_snapshot: dict[str, Any],
        credential_payload: dict[str, Any],
        platform_values: dict[str, Any],
    ) -> AgentInvocationResult:
        """Invoke an Agent according to its frozen snapshot."""
        mode = str(agent_snapshot.get("invokeMode") or agent_snapshot.get("invoke_mode") or "")
        if mode == "sync_response":
            return await self._invoke_sync(agent_snapshot, credential_payload, platform_values)
        if mode == "submit_poll":
            return await self._invoke_submit_poll(agent_snapshot, credential_payload, platform_values)
        raise AgentInvocationError(f"Unsupported invokeMode: {mode}")

    async def _invoke_sync(
        self,
        agent_snapshot: dict[str, Any],
        credential_payload: dict[str, Any],
        platform_values: dict[str, Any],
    ) -> AgentInvocationResult:
        connection = agent_snapshot["connection"]
        output_mapping = agent_snapshot["platformOutputMapping"]
        response_json = await self._post_json(agent_snapshot, credential_payload, platform_values)
        status = read_json_path(response_json, output_mapping.get("status")) or "completed"
        success_statuses = set(agent_snapshot.get("successStatuses") or ["completed"])
        return AgentInvocationResult(
            passed=str(status) in success_statuses,
            status=str(status),
            external_run_id=read_json_path(response_json, output_mapping.get("externalRunId")),
            final_answer=read_json_path(response_json, output_mapping.get("finalAnswer")),
            error_message=read_json_path(response_json, output_mapping.get("errorMessage")),
            raw_response=response_json,
        )

    async def _invoke_submit_poll(
        self,
        agent_snapshot: dict[str, Any],
        credential_payload: dict[str, Any],
        platform_values: dict[str, Any],
    ) -> AgentInvocationResult:
        connection = agent_snapshot["connection"]
        output_mapping = agent_snapshot["platformOutputMapping"]
        submit_json = await self._post_json(agent_snapshot, credential_payload, platform_values)
        external_run_id = read_json_path(submit_json, output_mapping.get("externalRunId"))
        if not external_run_id:
            raise AgentInvocationError(f"未能从响应路径 {output_mapping.get('externalRunId')} 解析 externalRunId。")

        terminal_statuses = set(agent_snapshot.get("terminalStatuses") or [])
        success_statuses = set(agent_snapshot.get("successStatuses") or [])
        poll_interval = float(connection.get("pollIntervalSeconds") or 0)
        poll_timeout = float(connection.get("pollTimeoutSeconds") or connection.get("requestTimeoutSeconds") or 30)
        deadline = asyncio.get_running_loop().time() + poll_timeout
        result_template = str(connection.get("resultPathTemplate") or "")
        if not result_template:
            raise AgentInvocationError("submit_poll 模式下 resultPathTemplate 为必填字段。")

        while True:
            poll_path = result_template.replace("{externalRunId}", str(external_run_id))
            poll_json = await self._request_json(
                "GET",
                _join_url(str(connection["baseUrl"]), poll_path),
                headers=_auth_headers(agent_snapshot.get("auth") or {}, credential_payload),
                json_body=None,
                timeout=float(connection.get("requestTimeoutSeconds") or 30),
            )
            status = read_json_path(poll_json, output_mapping.get("status"))
            if status is not None and str(status) in terminal_statuses:
                return AgentInvocationResult(
                    passed=str(status) in success_statuses,
                    status=str(status),
                    external_run_id=str(external_run_id),
                    final_answer=read_json_path(poll_json, output_mapping.get("finalAnswer")),
                    error_message=read_json_path(poll_json, output_mapping.get("errorMessage")),
                    raw_response=poll_json,
                )
            if asyncio.get_running_loop().time() >= deadline:
                raise AgentInvocationError("外部 Agent 轮询超时。")
            await asyncio.sleep(poll_interval)

    async def _post_json(
        self,
        agent_snapshot: dict[str, Any],
        credential_payload: dict[str, Any],
        platform_values: dict[str, Any],
    ) -> dict[str, Any]:
        connection = agent_snapshot["connection"]
        body = build_agent_request_body(
            custom_request_body=agent_snapshot.get("customRequestBody") or {},
            platform_input_mapping=agent_snapshot.get("platformInputMapping") or {},
            platform_values=platform_values,
        )
        return await self._request_json(
            "POST",
            _join_url(str(connection["baseUrl"]), str(connection["invokePath"])),
            headers=_auth_headers(agent_snapshot.get("auth") or {}, credential_payload),
            json_body=body,
            timeout=float(connection.get("requestTimeoutSeconds") or 30),
        )

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json_body: dict[str, Any] | None,
        timeout: float,
    ) -> dict[str, Any]:
        current_url = url
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout), follow_redirects=False, transport=self.transport) as client:
            for _ in range(settings.AGENT_HTTP_MAX_REDIRECTS + 1):
                response = await client.request(method, current_url, headers=headers, json=json_body)
                if response.is_redirect and response.headers.get("location"):
                    current_url = _join_url(str(response.url), response.headers["location"])
                    continue
                if len(response.content) > settings.AGENT_HTTP_RESPONSE_MAX_BYTES:
                    raise AgentInvocationError("外部 Agent 响应体过大。")
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise AgentInvocationError("外部 Agent 响应必须是 JSON 对象。")
                return payload
        raise AgentInvocationError("外部 Agent 重定向次数过多。")
