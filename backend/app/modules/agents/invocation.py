"""HTTP invocation client for registered external Agents."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from urllib.parse import urljoin

import httpx

from app.modules.agents.evidence import AgentInvocationEvidenceRecorder
from app.modules.agents.security import validate_agent_base_url
from app.platform.config import settings

LOGGER = logging.getLogger(__name__)


class AgentInvocationError(RuntimeError):
    """Raised when an external Agent call cannot complete."""

    def __init__(
        self,
        message: str,
        *,
        error_class: str = "error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_class = error_class
        self.details = details or {}


class AgentInvocationCanceled(AgentInvocationError):
    """Raised when the platform cancels an in-flight external Agent run."""


CancelRequested = Callable[[], Awaitable[bool]]


@dataclass(slots=True)
class AgentInvocationResult:
    """Normalized external Agent lifecycle result."""

    passed: bool
    status: str | None
    external_run_id: str | None
    final_answer: Any
    error_message: str | None
    raw_response: dict[str, Any]


@dataclass(slots=True)
class AgentSuccessEvaluation:
    """Result of checking external Agent success semantics."""

    passed: bool
    error_message: str | None


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


def _positive_float(value: Any) -> float | None:
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return None
    if candidate <= 0:
        return None
    return candidate


def _resolve_poll_timeout_seconds(
    connection: dict[str, Any], platform_values: dict[str, Any]
) -> float:
    """Resolve submit-poll deadline from the active run before agent defaults."""
    return (
        _positive_float(platform_values.get("timeoutSeconds"))
        or _positive_float(connection.get("pollTimeoutSeconds"))
        or _positive_float(connection.get("requestTimeoutSeconds"))
        or 30.0
    )


def render_platform_values(
    *,
    task_render_mode: str,
    platform_values: dict[str, Any],
) -> dict[str, Any]:
    """Render platform values before applying request field mappings."""
    rendered = dict(platform_values)
    if task_render_mode != "goal_with_entry_url":
        return rendered

    entry_url = rendered.get("entryUrl")
    entry_url_text = "" if entry_url is None else str(entry_url).strip()
    if not entry_url_text:
        return rendered

    task = rendered.get("task")
    task_text = "" if task is None else str(task).strip()
    rendered["task"] = (
        f"{task_text}\n\nStart URL: {entry_url_text}"
        if task_text
        else f"Start URL: {entry_url_text}"
    )
    return rendered


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


def evaluate_agent_success(
    *,
    status: Any,
    response_json: dict[str, Any],
    output_mapping: dict[str, str],
    success_statuses: set[str],
) -> AgentSuccessEvaluation:
    """Evaluate lifecycle status plus optional Boolean task success output."""
    if str(status) not in success_statuses:
        return AgentSuccessEvaluation(passed=False, error_message=None)

    success_path = output_mapping.get("success")
    if not success_path:
        return AgentSuccessEvaluation(passed=True, error_message=None)

    success_value = read_json_path(response_json, success_path)
    if success_value is True:
        return AgentSuccessEvaluation(passed=True, error_message=None)
    if success_value is False:
        return AgentSuccessEvaluation(
            passed=False,
            error_message="外部 Agent success 字段为 false。",
        )
    if success_value is None:
        return AgentSuccessEvaluation(
            passed=False,
            error_message=f"未能从响应路径 {success_path} 解析 success。",
        )
    return AgentSuccessEvaluation(
        passed=False,
        error_message=f"响应路径 {success_path} 必须是布尔值。",
    )


def _join_url(base_url: str, path: str) -> str:
    parsed_path = httpx.URL(path)
    if parsed_path.scheme and parsed_path.host:
        return validate_agent_base_url(path)
    base = validate_agent_base_url(base_url)
    return urljoin(f"{base}/", path.lstrip("/"))


def _auth_headers(
    auth: dict[str, Any], credential_payload: dict[str, Any]
) -> dict[str, str]:
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
        evidence_recorder: AgentInvocationEvidenceRecorder | None = None,
        cancel_requested: CancelRequested | None = None,
    ) -> AgentInvocationResult:
        """Invoke an Agent according to its frozen snapshot."""
        started = time.perf_counter()
        try:
            mode = str(
                agent_snapshot.get("invokeMode")
                or agent_snapshot.get("invoke_mode")
                or ""
            )
            if mode == "sync_response":
                result = await self._invoke_sync(
                    agent_snapshot,
                    credential_payload,
                    platform_values,
                    evidence_recorder,
                )
            elif mode == "submit_poll":
                result = await self._invoke_submit_poll(
                    agent_snapshot,
                    credential_payload,
                    platform_values,
                    evidence_recorder,
                    cancel_requested,
                )
            else:
                raise AgentInvocationError(
                    f"Unsupported invokeMode: {mode}",
                    error_class="unsupported_mode",
                )
            if evidence_recorder is not None:
                evidence_recorder.finish_success(result)
            LOGGER.info(
                "agent_invocation_completed",
                extra=_log_extra(
                    agent_snapshot,
                    platform_values,
                    duration_ms=_duration_ms(started),
                    status=result.status,
                    external_run_id=result.external_run_id,
                    passed=result.passed,
                ),
            )
            return result
        except AgentInvocationError as exc:
            if evidence_recorder is not None:
                evidence_recorder.finish_failure(
                    error_class=exc.error_class,
                    error_message=str(exc),
                    details=exc.details,
                )
            LOGGER.warning(
                "agent_invocation_failed",
                extra=_log_extra(
                    agent_snapshot,
                    platform_values,
                    duration_ms=_duration_ms(started),
                    error_class=exc.error_class,
                ),
            )
            raise
        except httpx.RequestError as exc:
            error = AgentInvocationError(str(exc), error_class="network_error")
            if evidence_recorder is not None:
                evidence_recorder.finish_failure(
                    error_class=error.error_class, error_message=str(error)
                )
            LOGGER.warning(
                "agent_invocation_failed",
                extra=_log_extra(
                    agent_snapshot,
                    platform_values,
                    duration_ms=_duration_ms(started),
                    error_class=error.error_class,
                ),
            )
            raise error from exc

    async def _invoke_sync(
        self,
        agent_snapshot: dict[str, Any],
        credential_payload: dict[str, Any],
        platform_values: dict[str, Any],
        evidence_recorder: AgentInvocationEvidenceRecorder | None = None,
    ) -> AgentInvocationResult:
        output_mapping = agent_snapshot["platformOutputMapping"]
        response_json = await self._post_json(
            agent_snapshot, credential_payload, platform_values, evidence_recorder
        )
        status = (
            read_json_path(response_json, output_mapping.get("status")) or "completed"
        )
        success_statuses = set(agent_snapshot.get("successStatuses") or ["completed"])
        success = evaluate_agent_success(
            status=status,
            response_json=response_json,
            output_mapping=output_mapping,
            success_statuses=success_statuses,
        )
        error_message = read_json_path(
            response_json, output_mapping.get("errorMessage")
        )
        return AgentInvocationResult(
            passed=success.passed,
            status=str(status),
            external_run_id=read_json_path(
                response_json, output_mapping.get("externalRunId")
            ),
            final_answer=read_json_path(
                response_json, output_mapping.get("finalAnswer")
            ),
            error_message=error_message or success.error_message,
            raw_response=response_json,
        )

    async def _invoke_submit_poll(
        self,
        agent_snapshot: dict[str, Any],
        credential_payload: dict[str, Any],
        platform_values: dict[str, Any],
        evidence_recorder: AgentInvocationEvidenceRecorder | None = None,
        cancel_requested: CancelRequested | None = None,
    ) -> AgentInvocationResult:
        connection = agent_snapshot["connection"]
        output_mapping = agent_snapshot["platformOutputMapping"]
        submit_json = await self._post_json(
            agent_snapshot, credential_payload, platform_values, evidence_recorder
        )
        external_run_id = read_json_path(
            submit_json, output_mapping.get("externalRunId")
        )
        if not external_run_id:
            raise AgentInvocationError(
                f"未能从响应路径 {output_mapping.get('externalRunId')} 解析 externalRunId。",
                error_class="mapping_error",
            )

        terminal_statuses = set(agent_snapshot.get("terminalStatuses") or [])
        success_statuses = set(agent_snapshot.get("successStatuses") or [])
        poll_interval = float(connection.get("pollIntervalSeconds") or 0)
        poll_timeout = _resolve_poll_timeout_seconds(connection, platform_values)
        deadline = asyncio.get_running_loop().time() + poll_timeout
        result_template = str(connection.get("resultPathTemplate") or "")
        if not result_template:
            raise AgentInvocationError(
                "submit_poll 模式下 resultPathTemplate 为必填字段。"
            )

        while True:
            if cancel_requested is not None and await cancel_requested():
                cancel_error: str | None = None
                try:
                    await self._cancel_external_run(
                        agent_snapshot=agent_snapshot,
                        credential_payload=credential_payload,
                        external_run_id=str(external_run_id),
                        evidence_recorder=evidence_recorder,
                    )
                except (AgentInvocationError, httpx.RequestError) as exc:
                    cancel_error = str(exc)
                    LOGGER.warning(
                        "agent_invocation_cancel_failed",
                        extra=_log_extra(
                            agent_snapshot,
                            platform_values,
                            duration_ms=0,
                            external_run_id=str(external_run_id),
                            error_class=(
                                exc.error_class
                                if isinstance(exc, AgentInvocationError)
                                else "network_error"
                            ),
                        ),
                    )
                details = {
                    "status": "canceled",
                    "externalRunId": str(external_run_id),
                }
                if cancel_error:
                    details["cancelError"] = cancel_error
                raise AgentInvocationCanceled(
                    "外部 Agent 调用已取消。",
                    error_class="canceled",
                    details=details,
                )
            poll_path = result_template.replace("{externalRunId}", str(external_run_id))
            poll_json = await self._request_json(
                "GET",
                _join_url(str(connection["baseUrl"]), poll_path),
                headers=_auth_headers(
                    agent_snapshot.get("auth") or {}, credential_payload
                ),
                json_body=None,
                timeout=float(connection.get("requestTimeoutSeconds") or 30),
                evidence_recorder=evidence_recorder,
            )
            status = read_json_path(poll_json, output_mapping.get("status"))
            if status is not None and str(status) in terminal_statuses:
                success = evaluate_agent_success(
                    status=status,
                    response_json=poll_json,
                    output_mapping=output_mapping,
                    success_statuses=success_statuses,
                )
                error_message = read_json_path(
                    poll_json, output_mapping.get("errorMessage")
                )
                return AgentInvocationResult(
                    passed=success.passed,
                    status=str(status),
                    external_run_id=str(external_run_id),
                    final_answer=read_json_path(
                        poll_json, output_mapping.get("finalAnswer")
                    ),
                    error_message=error_message or success.error_message,
                    raw_response=poll_json,
                )
            if asyncio.get_running_loop().time() >= deadline:
                raise AgentInvocationError(
                    "外部 Agent 轮询超时。",
                    error_class="poll_timeout",
                    details={"externalRunId": str(external_run_id)},
                )
            await asyncio.sleep(poll_interval)

    async def _cancel_external_run(
        self,
        *,
        agent_snapshot: dict[str, Any],
        credential_payload: dict[str, Any],
        external_run_id: str,
        evidence_recorder: AgentInvocationEvidenceRecorder | None = None,
    ) -> None:
        connection = agent_snapshot["connection"]
        cancel_path_template = connection.get("cancelPathTemplate")
        if not cancel_path_template:
            return
        cancel_path = str(cancel_path_template).replace(
            "{externalRunId}", external_run_id
        )
        cancel_body = connection.get("cancelRequestBody")
        await self._request_json(
            str(connection.get("cancelMethod") or "POST").upper(),
            _join_url(str(connection["baseUrl"]), cancel_path),
            headers=_auth_headers(agent_snapshot.get("auth") or {}, credential_payload),
            json_body=cancel_body if isinstance(cancel_body, dict) else None,
            timeout=float(connection.get("requestTimeoutSeconds") or 30),
            evidence_recorder=evidence_recorder,
            expect_json=False,
        )

    async def _post_json(
        self,
        agent_snapshot: dict[str, Any],
        credential_payload: dict[str, Any],
        platform_values: dict[str, Any],
        evidence_recorder: AgentInvocationEvidenceRecorder | None = None,
    ) -> dict[str, Any]:
        connection = agent_snapshot["connection"]
        body = build_agent_request_body(
            custom_request_body=agent_snapshot.get("customRequestBody") or {},
            platform_input_mapping=agent_snapshot.get("platformInputMapping") or {},
            platform_values=render_platform_values(
                task_render_mode=str(agent_snapshot.get("taskRenderMode") or ""),
                platform_values=platform_values,
            ),
        )
        return await self._request_json(
            "POST",
            _join_url(str(connection["baseUrl"]), str(connection["invokePath"])),
            headers=_auth_headers(agent_snapshot.get("auth") or {}, credential_payload),
            json_body=body,
            timeout=float(connection.get("requestTimeoutSeconds") or 30),
            evidence_recorder=evidence_recorder,
        )

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json_body: dict[str, Any] | None,
        timeout: float,
        evidence_recorder: AgentInvocationEvidenceRecorder | None = None,
        expect_json: bool = True,
    ) -> dict[str, Any]:
        current_url = url
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=False,
            transport=self.transport,
        ) as client:
            for _ in range(settings.AGENT_HTTP_MAX_REDIRECTS + 1):
                started = time.perf_counter()
                call_id = (
                    evidence_recorder.start_http_call(
                        method=method,
                        url=current_url,
                        headers=headers,
                        json_body=json_body,
                    )
                    if evidence_recorder is not None
                    else None
                )
                try:
                    response = await client.request(
                        method, current_url, headers=headers, json=json_body
                    )
                except httpx.RequestError as exc:
                    if evidence_recorder is not None and call_id is not None:
                        evidence_recorder.fail_http_call(
                            call_id,
                            error_class="network_error",
                            error_message=str(exc),
                            duration_ms=_duration_ms(started),
                        )
                    raise
                if response.is_redirect and response.headers.get("location"):
                    if evidence_recorder is not None and call_id is not None:
                        evidence_recorder.complete_http_call(
                            call_id,
                            response=response,
                            duration_ms=_duration_ms(started),
                        )
                    current_url = _join_url(
                        str(response.url), response.headers["location"]
                    )
                    continue
                if len(response.content) > settings.AGENT_HTTP_RESPONSE_MAX_BYTES:
                    if evidence_recorder is not None and call_id is not None:
                        evidence_recorder.fail_http_call(
                            call_id,
                            error_class="response_too_large",
                            error_message="外部 Agent 响应体过大。",
                            duration_ms=_duration_ms(started),
                            response=response,
                        )
                    raise AgentInvocationError(
                        "外部 Agent 响应体过大。",
                        error_class="response_too_large",
                    )
                if response.status_code >= 400:
                    if evidence_recorder is not None and call_id is not None:
                        evidence_recorder.fail_http_call(
                            call_id,
                            error_class="http_error",
                            error_message=f"HTTP {response.status_code}",
                            duration_ms=_duration_ms(started),
                            response=response,
                        )
                    raise AgentInvocationError(
                        f"外部 Agent HTTP 调用失败: HTTP {response.status_code}",
                        error_class="http_error",
                    )
                if not expect_json:
                    if evidence_recorder is not None and call_id is not None:
                        evidence_recorder.complete_http_call(
                            call_id,
                            response=response,
                            duration_ms=_duration_ms(started),
                        )
                    return {}
                try:
                    payload = response.json()
                except ValueError as exc:
                    if evidence_recorder is not None and call_id is not None:
                        evidence_recorder.fail_http_call(
                            call_id,
                            error_class="invalid_json",
                            error_message="外部 Agent 响应必须是 JSON 对象。",
                            duration_ms=_duration_ms(started),
                            response=response,
                        )
                    raise AgentInvocationError(
                        "外部 Agent 响应必须是 JSON 对象。",
                        error_class="invalid_json",
                    ) from exc
                if not isinstance(payload, dict):
                    if evidence_recorder is not None and call_id is not None:
                        evidence_recorder.fail_http_call(
                            call_id,
                            error_class="invalid_json",
                            error_message="外部 Agent 响应必须是 JSON 对象。",
                            duration_ms=_duration_ms(started),
                            response=response,
                        )
                    raise AgentInvocationError(
                        "外部 Agent 响应必须是 JSON 对象。",
                        error_class="invalid_json",
                    )
                if evidence_recorder is not None and call_id is not None:
                    evidence_recorder.complete_http_call(
                        call_id,
                        response=response,
                        duration_ms=_duration_ms(started),
                    )
                return payload
        raise AgentInvocationError(
            "外部 Agent 重定向次数过多。", error_class="redirect_limit"
        )


def _duration_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _log_extra(
    agent_snapshot: dict[str, Any],
    platform_values: dict[str, Any],
    *,
    duration_ms: int,
    status: str | None = None,
    external_run_id: str | None = None,
    passed: bool | None = None,
    error_class: str | None = None,
) -> dict[str, Any]:
    return {
        "agent_id": agent_snapshot.get("agentId"),
        "template_id": agent_snapshot.get("templateId"),
        "invoke_mode": agent_snapshot.get("invokeMode")
        or agent_snapshot.get("invoke_mode"),
        "evaluation_id": platform_values.get("evaluationId"),
        "sample_id": platform_values.get("sampleId"),
        "status": status,
        "external_run_id": external_run_id,
        "passed": passed,
        "duration_ms": duration_ms,
        "error_class": error_class,
    }
