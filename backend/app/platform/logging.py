"""Logging setup helpers for API, scheduler and worker processes."""

from __future__ import annotations

import contextvars
import json
import logging
import re
import traceback
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.platform.config import settings

_CONFIGURED = False
_LOG_CONTEXT: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "asp_log_context", default={}
)

SENSITIVE_KEY_FRAGMENTS = (
    "authorization",
    "cookie",
    "credential",
    "password",
    "secret",
    "set-cookie",
    "token",
    "api_key",
    "apikey",
)
REDACTED = "[REDACTED]"
MAX_LOG_STRING_LENGTH = 2_000
_SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(authorization|cookie|set-cookie|api[_-]?key|token|secret|password|credential)"
    r"(\s*[:=]\s*)([^\s,;&\"'}]+)"
)
_BEARER_RE = re.compile(r"(?i)\b(bearer\s+)([A-Za-z0-9._~+/=-]+)")
_URL_USERINFO_RE = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)([^/\s:@]+):([^/\s@]+)@")
_RESERVED_RECORD_ATTRS = set(
    logging.LogRecord(
        name="",
        level=0,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__
)
_RESERVED_RECORD_ATTRS.update({"message", "asctime"})
_EXCLUDED_EXTRA_ATTRS = {"color_message"}
_EXTRA_KEY_ALIASES = {
    "agent_id": "agentId",
    "dataset_id": "datasetId",
    "duration_ms": "durationMs",
    "error_class": "errorClass",
    "error_code": "errorCode",
    "evaluation_id": "evaluationId",
    "external_run_id": "externalRunId",
    "invoke_mode": "invokeMode",
    "latency_ms": "durationMs",
    "request_id": "requestId",
    "run_id": "runId",
    "sample_execution_id": "sampleExecutionId",
    "sample_id": "sampleId",
    "source_ip": "clientIp",
    "status_code": "statusCode",
    "template_id": "templateId",
    "token_result": "tokenResult",
    "trace_id": "traceId",
    "worker_id": "workerId",
}


def _is_sensitive_key(key: object) -> bool:
    lowered = str(key).lower().replace("-", "_")
    return any(fragment.replace("-", "_") in lowered for fragment in SENSITIVE_KEY_FRAGMENTS)


def _truncate(value: str) -> str:
    if len(value) <= MAX_LOG_STRING_LENGTH:
        return value
    return f"{value[:MAX_LOG_STRING_LENGTH]}...[truncated]"


def _redact_sensitive_text(value: str) -> str:
    value = _BEARER_RE.sub(r"\1[REDACTED]", value)
    value = _SENSITIVE_ASSIGNMENT_RE.sub(r"\1\2[REDACTED]", value)
    return _URL_USERINFO_RE.sub(r"\1[REDACTED]@", value)


def _sanitize_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return _truncate(value)
    if not parsed.scheme or not parsed.netloc:
        return _truncate(value)
    query_items = [
        (key, REDACTED if _is_sensitive_key(key) else item_value)
        for key, item_value in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    netloc = parsed.hostname or ""
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    return _truncate(
        urlunsplit(
            (
                parsed.scheme,
                netloc,
                parsed.path,
                urlencode(query_items),
                parsed.fragment,
            )
        )
    )


def sanitize_query_string(value: str) -> str:
    """Return a query string with sensitive values redacted."""
    query_items = [
        (key, REDACTED if _is_sensitive_key(key) else item_value)
        for key, item_value in parse_qsl(value, keep_blank_values=True)
    ]
    return urlencode(query_items)


def sanitize_for_log(value: Any) -> Any:
    """Recursively sanitize values before they are written to logs or audit payloads."""
    if isinstance(value, Mapping):
        return {
            str(key): REDACTED if _is_sensitive_key(key) else sanitize_for_log(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(sanitize_for_log(item) for item in value)
    if isinstance(value, list):
        return [sanitize_for_log(item) for item in value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_for_log(item) for item in value]
    if isinstance(value, str):
        redacted = _redact_sensitive_text(value)
        if "://" in redacted:
            return _sanitize_url(redacted)
        return _truncate(redacted)
    return value


def bind_log_context(**values: Any) -> contextvars.Token[dict[str, Any]]:
    """Bind structured fields to logs emitted in the current async context."""
    current = dict(_LOG_CONTEXT.get())
    current.update({key: item for key, item in values.items() if item is not None})
    return _LOG_CONTEXT.set(current)


def reset_log_context(token: contextvars.Token[dict[str, Any]]) -> None:
    """Reset a context token returned by bind_log_context."""
    _LOG_CONTEXT.reset(token)


def current_log_context() -> dict[str, Any]:
    """Return the structured log context for the current task."""
    return dict(_LOG_CONTEXT.get())


class JsonLogFormatter(logging.Formatter):
    """Render stdlib LogRecords as one JSON object per line."""

    def __init__(self, *, env: str | None = None, service: str | None = None) -> None:
        super().__init__()
        self.env = env or getattr(settings, "LOG_ENV", "dev")
        self.service = service or getattr(settings, "LOG_SERVICE_NAME", "backend")

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "service": getattr(record, "service", self.service),
            "env": self.env,
            "logger": record.name,
            "event": getattr(record, "event", None) or record.getMessage(),
            "message": record.getMessage(),
        }
        payload.update(current_log_context())
        for key, value in record.__dict__.items():
            normalized_key = _EXTRA_KEY_ALIASES.get(key, key)
            if (
                key in _RESERVED_RECORD_ATTRS
                or key in _EXCLUDED_EXTRA_ATTRS
                or normalized_key in payload
            ):
                continue
            payload[normalized_key] = value
        if record.exc_info:
            exc_type = record.exc_info[0]
            payload.setdefault(
                "errorClass", exc_type.__name__ if exc_type is not None else None
            )
            payload["traceback"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(sanitize_for_log(payload), ensure_ascii=False, default=str)


def configure_logging(*, force: bool = False) -> None:
    """Configure stdlib logging once per process."""
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    level_name = (settings.LOG_LEVEL or "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)
    handler = logging.StreamHandler()
    if str(getattr(settings, "LOG_FORMAT", "text")).strip().lower() == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
    _CONFIGURED = True
