from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from app.modules.runtime_gateway import router as runtime_gateway_router
from app.modules.runtime_gateway.session_store import (
    RuntimeSessionView,
    hash_runtime_token,
)


def _active_session() -> RuntimeSessionView:
    return RuntimeSessionView(
        sample_execution_id=123,
        internal_base_url="http://asp-runtime-rt_123:8000",
        public_entry_url="https://platform.example.com/runtime/tasks/123/",
        token_hash=hash_runtime_token("runtime-token"),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        status="active",
    )


def test_runtime_gateway_proxies_authorized_request_and_sets_scoped_cookie(
    client,
    monkeypatch,
) -> None:
    captured_requests: list[httpx.Request] = []

    async def fake_authorize_runtime_request(
        *, sample_execution_id: int, query_token: str | None, cookie_token: str | None
    ):
        assert sample_execution_id == 123
        assert query_token == "runtime-token"
        assert cookie_token is None
        return _active_session(), "query"

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            200,
            headers={
                "content-type": "text/html; charset=utf-8",
                "connection": "keep-alive",
            },
            text='<html><head><script src="/__probe__/probe.js"></script></head>'
            '<body><a href="/next.html">next</a></body></html>',
        )

    monkeypatch.setattr(
        runtime_gateway_router,
        "authorize_runtime_request",
        fake_authorize_runtime_request,
    )
    monkeypatch.setattr(
        runtime_gateway_router,
        "build_runtime_proxy_client",
        lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(handler), follow_redirects=False
        ),
    )

    response = client.get(
        "/runtime/tasks/123/Sample_1/site/index.html?token=runtime-token&debug=1",
        headers={"X-Forwarded-For": "203.0.113.10"},
    )

    assert response.status_code == 200
    assert captured_requests[0].url == (
        "http://asp-runtime-rt_123:8000/Sample_1/site/index.html?debug=1"
    )
    assert "connection" not in response.headers
    assert "/runtime/tasks/123/__probe__/probe.js" in response.text
    assert 'href="/runtime/tasks/123/next.html"' in response.text
    assert "asp_runtime_token=runtime-token" in response.headers["set-cookie"]
    assert "Path=/runtime/tasks/123" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]


def test_runtime_gateway_accepts_scoped_cookie_without_query_token(
    client,
    monkeypatch,
) -> None:
    captured_requests: list[httpx.Request] = []

    async def fake_authorize_runtime_request(
        *, sample_execution_id: int, query_token: str | None, cookie_token: str | None
    ):
        assert sample_execution_id == 123
        assert query_token is None
        assert cookie_token == "runtime-token"
        return _active_session(), "cookie"

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(204)

    monkeypatch.setattr(
        runtime_gateway_router,
        "authorize_runtime_request",
        fake_authorize_runtime_request,
    )
    monkeypatch.setattr(
        runtime_gateway_router,
        "build_runtime_proxy_client",
        lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(handler), follow_redirects=False
        ),
    )

    response = client.post(
        "/runtime/tasks/123/__probe__/collect",
        content=b'{"ok": true}',
        headers={
            "content-type": "application/json",
            "cookie": "asp_runtime_token=runtime-token",
        },
    )

    assert response.status_code == 204
    assert (
        captured_requests[0].url
        == "http://asp-runtime-rt_123:8000/__probe__/collect"
    )
    assert captured_requests[0].content == b'{"ok": true}'
    assert "set-cookie" not in response.headers


def test_runtime_gateway_rejects_invalid_or_missing_token(client, monkeypatch) -> None:
    async def fake_authorize_runtime_request(
        *, sample_execution_id: int, query_token: str | None, cookie_token: str | None
    ):
        return None, "invalid"

    monkeypatch.setattr(
        runtime_gateway_router,
        "authorize_runtime_request",
        fake_authorize_runtime_request,
    )

    response = client.get("/runtime/tasks/123/index.html")

    assert response.status_code == 403
    assert response.json()["message"] == "runtime session is not authorized"
