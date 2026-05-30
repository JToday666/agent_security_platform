"""HTTP request logging middleware with request and trace identifiers."""

from __future__ import annotations

import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.platform.logging import (
    bind_log_context,
    reset_log_context,
    sanitize_query_string,
)

LOGGER = logging.getLogger(__name__)


def _request_id_from_header(request: Request) -> str:
    value = request.headers.get("X-Request-ID")
    if value and len(value) <= 128:
        return value
    return f"req_{uuid4().hex}"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach request IDs to responses and write sanitized API access logs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = _request_id_from_header(request)
        trace_id = request.headers.get("X-Trace-ID") or request_id
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        token = bind_log_context(requestId=request_id, traceId=trace_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            LOGGER.info(
                "http.request.completed",
                extra={
                    "event": "http.request.completed",
                    "requestId": request_id,
                    "traceId": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query": sanitize_query_string(request.url.query),
                    "statusCode": status_code,
                    "durationMs": int((time.perf_counter() - started) * 1000),
                    "clientIp": request.client.host if request.client else None,
                },
            )
            reset_log_context(token)
