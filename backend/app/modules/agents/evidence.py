"""Redacted evidence recording for external Agent HTTP invocations."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from app.platform.config import settings

REDACTED = "[redacted]"
SENSITIVE_KEY_FRAGMENTS = {
    "api-key",
    "apikey",
    "api_key",
    "authorization",
    "cookie",
    "credential",
    "password",
    "secret",
    "set-cookie",
    "token",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("_", "-")
    return any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)


def redact_value(value: Any) -> Any:
    """Recursively redact sensitive keys while preserving useful structure."""
    if isinstance(value, dict):
        return {
            str(key): REDACTED if _is_sensitive_key(key) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    return value


def redact_headers(headers: dict[str, Any] | httpx.Headers | None) -> dict[str, str]:
    """Return a redacted, JSON-friendly header mapping."""
    if not headers:
        return {}
    return {
        str(key): REDACTED if _is_sensitive_key(key) else str(value)
        for key, value in dict(headers).items()
    }


def redact_url(url: str) -> str:
    """Remove URL userinfo and redact all query parameter values."""
    parts = urlsplit(str(url))
    hostname = parts.hostname or ""
    netloc = hostname
    if ":" in netloc and not netloc.startswith("["):
        netloc = f"[{netloc}]"
    if parts.port is not None:
        netloc = f"{netloc}:{parts.port}"
    query = urlencode(
        [(key, REDACTED) for key, _ in parse_qsl(parts.query, keep_blank_values=True)]
    )
    return urlunsplit((parts.scheme, netloc, parts.path, query, ""))


def _safe_json_from_response(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        text = response.text
        return text


class AgentInvocationEvidenceRecorder:
    """Accumulates sanitized external Agent HTTP evidence and writes it to disk."""

    def __init__(
        self,
        *,
        path: Path,
        agent_snapshot: dict[str, Any],
        platform_values: dict[str, Any],
        max_body_chars: int | None = None,
    ) -> None:
        self.path = path
        self.agent_snapshot = agent_snapshot
        self.platform_values = platform_values
        self.max_body_chars = int(
            max_body_chars or settings.AGENT_HTTP_EVIDENCE_MAX_BODY_CHARS
        )
        self.started_at = _utc_now()
        self.started_monotonic = time.perf_counter()
        self.http_calls: list[dict[str, Any]] = []
        self.outcome: dict[str, Any] = {"status": "running"}

    def start_http_call(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        json_body: dict[str, Any] | None,
    ) -> int:
        """Record the start of one outbound HTTP call."""
        call = {
            "startedAt": _iso(_utc_now()),
            "method": method.upper(),
            "url": redact_url(url),
            "requestHeaders": redact_headers(headers),
            "requestBodyPreview": self._body_preview(json_body),
            "responseStatusCode": None,
            "responseHeaders": {},
            "responseBodyPreview": None,
            "durationMs": None,
            "errorClass": None,
            "errorMessage": None,
        }
        self.http_calls.append(call)
        self.write()
        return len(self.http_calls) - 1

    def complete_http_call(
        self,
        call_id: int,
        *,
        response: httpx.Response,
        duration_ms: int,
    ) -> None:
        """Record a successful HTTP response for one call."""
        call = self.http_calls[call_id]
        call["responseStatusCode"] = response.status_code
        call["responseHeaders"] = redact_headers(response.headers)
        call["responseBodyPreview"] = self._body_preview(_safe_json_from_response(response))
        call["durationMs"] = duration_ms
        self.write()

    def fail_http_call(
        self,
        call_id: int,
        *,
        error_class: str,
        error_message: str,
        duration_ms: int,
        response: httpx.Response | None = None,
    ) -> None:
        """Record a failed HTTP call without exposing raw sensitive payloads."""
        call = self.http_calls[call_id]
        call["durationMs"] = duration_ms
        call["errorClass"] = error_class
        call["errorMessage"] = error_message[:500]
        if response is not None:
            call["responseStatusCode"] = response.status_code
            call["responseHeaders"] = redact_headers(response.headers)
            call["responseBodyPreview"] = self._body_preview(
                _safe_json_from_response(response)
            )
        self.write()

    def finish_success(self, result: Any) -> None:
        """Mark the overall invocation as complete."""
        self.outcome = {
            "status": getattr(result, "status", None),
            "passed": bool(getattr(result, "passed", False)),
            "externalRunId": getattr(result, "external_run_id", None),
            "errorClass": None,
            "errorMessage": getattr(result, "error_message", None),
        }
        self.write()

    def finish_failure(
        self,
        *,
        error_class: str,
        error_message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Mark the overall invocation as failed."""
        self.outcome = {
            "status": "failed",
            "passed": False,
            "errorClass": error_class,
            "errorMessage": error_message[:500],
        }
        if details:
            self.outcome.update(redact_value(details))
        self.write()

    def write(self) -> None:
        """Write the current evidence payload to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.payload(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def payload(self) -> dict[str, Any]:
        """Build the full evidence document."""
        finished_at = _utc_now()
        return {
            "schemaVersion": 1,
            "agentId": self.agent_snapshot.get("agentId"),
            "templateId": self.agent_snapshot.get("templateId"),
            "invokeMode": self.agent_snapshot.get("invokeMode")
            or self.agent_snapshot.get("invoke_mode"),
            "evaluationId": self.platform_values.get("evaluationId"),
            "sampleId": self.platform_values.get("sampleId"),
            "startedAt": _iso(self.started_at),
            "finishedAt": _iso(finished_at),
            "durationMs": int((time.perf_counter() - self.started_monotonic) * 1000),
            "outcome": self.outcome,
            "httpCalls": self.http_calls,
        }

    def _body_preview(self, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        redacted = redact_value(value)
        text = json.dumps(redacted, ensure_ascii=False, sort_keys=True)
        truncated = len(text) > self.max_body_chars
        if truncated:
            text = text[: self.max_body_chars]
        return {
            "truncated": truncated,
            "body": json.loads(text) if not truncated else text,
        }
