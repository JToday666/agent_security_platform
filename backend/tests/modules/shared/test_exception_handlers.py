from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.shared.errors import NotFoundError
from app.shared.exception_handlers import _loc_to_field, register_exception_handlers


def build_exception_test_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/domain-error")
    async def domain_error_route():
        raise NotFoundError("not found")

    @app.get("/http-error")
    async def http_error_route():
        raise HTTPException(status_code=418, detail="teapot")

    @app.get("/wrapped-http-error")
    async def wrapped_http_error_route():
        raise HTTPException(status_code=400, detail={"code": 40001, "message": "bad request", "data": {"x": 1}})

    @app.get("/crash")
    async def crash_route():
        raise RuntimeError("boom")

    return TestClient(app, raise_server_exceptions=False)


def test_loc_to_field_converts_fastapi_locations() -> None:
    assert _loc_to_field(("body", "items", 0, "name")) == "items.0.name"
    assert _loc_to_field(("query", "page")) == "page"
    assert _loc_to_field(("body",)) == "request"


def test_domain_and_http_exceptions_use_wrapped_responses() -> None:
    client = build_exception_test_client()

    domain_response = client.get("/domain-error")
    assert domain_response.status_code == 404
    assert domain_response.json() == {"code": 40400, "data": None, "message": "not found"}

    http_response = client.get("/http-error")
    assert http_response.status_code == 418
    assert http_response.json() == {"code": 418, "data": None, "message": "teapot"}

    wrapped_http_response = client.get("/wrapped-http-error")
    assert wrapped_http_response.status_code == 400
    assert wrapped_http_response.json() == {"code": 40001, "data": {"x": 1}, "message": "bad request"}


def test_unhandled_exceptions_use_internal_error_envelope() -> None:
    client = build_exception_test_client()
    response = client.get("/crash")

    assert response.status_code == 500
    assert response.json() == {
        "code": 50000,
        "data": {"errorType": "RuntimeError"},
        "message": "服务内部错误，请稍后重试。",
    }
