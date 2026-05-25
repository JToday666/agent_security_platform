"""Public runtime gateway proxy routes."""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Iterable
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.modules.runtime_gateway.session_store import (
    RuntimeSessionView,
    authorize_runtime_request,
)
from app.platform.config import settings
from app.platform.http import json_error_response

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/runtime", tags=["runtime-gateway"])

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
REQUEST_HEADER_BLOCKLIST = HOP_BY_HOP_HEADERS | {"host", "content-length"}
RESPONSE_HEADER_BLOCKLIST = HOP_BY_HOP_HEADERS | {"content-length"}
HTML_ABSOLUTE_ATTR_RE = re.compile(
    r'(?P<prefix>\b(?:src|href|action)=["\'])/'
    r"(?!(?:/|runtime/tasks/|api/|uploads/|healthz|readyz))",
    flags=re.IGNORECASE,
)


def build_runtime_proxy_client() -> httpx.AsyncClient:
    """Build the outbound client used to proxy runtime requests."""
    return httpx.AsyncClient(follow_redirects=False, timeout=httpx.Timeout(30.0))


def _gateway_prefix(sample_execution_id: int) -> str:
    return f"/runtime/tasks/{sample_execution_id}"


def _filter_headers(
    headers: Iterable[tuple[str, str]], *, response: bool = False
) -> dict[str, str]:
    blocklist = RESPONSE_HEADER_BLOCKLIST if response else REQUEST_HEADER_BLOCKLIST
    return {key: value for key, value in headers if key.lower() not in blocklist}


def _upstream_url(
    session: RuntimeSessionView,
    path: str,
    query_items: list[tuple[str, str]],
) -> str:
    upstream_path = f"/{path}" if path else "/"
    parsed_base = urlsplit(session.internal_base_url.rstrip("/"))
    query = urlencode(query_items)
    return urlunsplit(
        (
            parsed_base.scheme,
            parsed_base.netloc,
            f"{parsed_base.path.rstrip('/')}{upstream_path}",
            query,
            "",
        )
    )


def _rewrite_location_header(
    value: str, *, session: RuntimeSessionView, sample_execution_id: int
) -> str:
    parsed = urlsplit(value)
    prefix = _gateway_prefix(sample_execution_id)
    if parsed.scheme and parsed.netloc:
        base = urlsplit(session.internal_base_url)
        if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
            return value
    path = parsed.path or "/"
    return urlunsplit(("", "", f"{prefix}{path}", parsed.query, parsed.fragment))


def _rewrite_body(
    body: bytes, *, content_type: str, sample_execution_id: int
) -> bytes:
    if not body:
        return body
    lowered = content_type.lower()
    if "text/html" not in lowered and "javascript" not in lowered:
        return body
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return body

    prefix = _gateway_prefix(sample_execution_id)
    text = text.replace('"/__probe__', f'"{prefix}/__probe__')
    text = text.replace("'/__probe__", f"'{prefix}/__probe__")
    if "text/html" in lowered:
        text = HTML_ABSOLUTE_ATTR_RE.sub(rf"\g<prefix>{prefix}/", text)
    return text.encode("utf-8")


def _response_headers(
    upstream_response: httpx.Response,
    *,
    session: RuntimeSessionView,
    sample_execution_id: int,
) -> dict[str, str]:
    headers = _filter_headers(upstream_response.headers.multi_items(), response=True)
    location = headers.get("location") or headers.get("Location")
    if location:
        rewritten = _rewrite_location_header(
            location, session=session, sample_execution_id=sample_execution_id
        )
        headers.pop("location", None)
        headers.pop("Location", None)
        headers["location"] = rewritten
    return headers


def _cookie_max_age(session: RuntimeSessionView) -> int:
    return max(0, int((session.expires_at - time_now()).total_seconds()))


def time_now():
    from app.modules.runtime_gateway.session_store import now_utc

    return now_utc()


def _auth_error_status(
    token_source: str, *, query_token: str | None, cookie_token: str | None
) -> int:
    if token_source == "missing" and not query_token and not cookie_token:
        return 404
    return 403


def _set_runtime_cookie(
    response: Response,
    *,
    sample_execution_id: int,
    token: str,
    session: RuntimeSessionView,
) -> None:
    response.set_cookie(
        settings.RUNTIME_GATEWAY_COOKIE_NAME,
        token,
        max_age=_cookie_max_age(session),
        path=_gateway_prefix(sample_execution_id),
        httponly=True,
        secure=str(settings.PUBLIC_BASE_URL).startswith("https://"),
        samesite="lax",
    )


async def _proxy_runtime_request(
    request: Request, *, sample_execution_id: int, path: str
) -> Response:
    started = time.perf_counter()
    query_token = request.query_params.get("token")
    cookie_token = request.cookies.get(settings.RUNTIME_GATEWAY_COOKIE_NAME)
    session, token_source = await authorize_runtime_request(
        sample_execution_id=sample_execution_id,
        query_token=query_token,
        cookie_token=cookie_token,
    )
    if session is None:
        status_code = _auth_error_status(
            token_source, query_token=query_token, cookie_token=cookie_token
        )
        LOGGER.warning(
            "runtime_gateway_auth_failed",
            extra={
                "sample_execution_id": sample_execution_id,
                "path": path,
                "method": request.method,
                "source_ip": request.client.host if request.client else None,
                "token_result": token_source,
                "status_code": status_code,
                "latency_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        return json_error_response(
            http_status=status_code,
            code=40301,
            message="runtime session is not authorized",
        )

    query_items = [
        (key, value)
        for key, value in request.query_params.multi_items()
        if key != "token"
    ]
    upstream_url = _upstream_url(session, path, query_items)
    headers = _filter_headers(request.headers.items())
    body = await request.body()

    async with build_runtime_proxy_client() as client:
        upstream_response = await client.request(
            request.method,
            upstream_url,
            headers=headers,
            content=body,
        )

    response_headers = _response_headers(
        upstream_response,
        session=session,
        sample_execution_id=sample_execution_id,
    )
    content_type = upstream_response.headers.get("content-type", "")
    body = _rewrite_body(
        upstream_response.content,
        content_type=content_type,
        sample_execution_id=sample_execution_id,
    )
    response = Response(
        content=body,
        status_code=upstream_response.status_code,
        headers=response_headers,
    )
    if token_source == "query" and query_token:
        _set_runtime_cookie(
            response,
            sample_execution_id=sample_execution_id,
            token=query_token,
            session=session,
        )

    LOGGER.info(
        "runtime_gateway_proxy",
        extra={
            "sample_execution_id": sample_execution_id,
            "path": path,
            "method": request.method,
            "status_code": upstream_response.status_code,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "source_ip": request.client.host if request.client else None,
            "token_result": token_source,
        },
    )
    return response


@router.api_route(
    "/tasks/{sample_execution_id}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_runtime_root(request: Request, sample_execution_id: int) -> Response:
    """Proxy the root path of a runtime session."""
    return await _proxy_runtime_request(
        request, sample_execution_id=sample_execution_id, path=""
    )


@router.api_route(
    "/tasks/{sample_execution_id}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_runtime_path(
    request: Request, sample_execution_id: int, path: str
) -> Response:
    """Proxy an arbitrary path into one runtime session."""
    return await _proxy_runtime_request(
        request, sample_execution_id=sample_execution_id, path=path
    )
