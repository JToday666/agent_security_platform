from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.modules.evaluations.schemas import EvaluationCreateRequest
from app.platform.errors import NotFoundError
from app.platform.exception_handlers import (
    _loc_to_field,
    _validation_reason,
    register_exception_handlers,
)
from app.platform.i18n import LocaleMiddleware


class ValidationPayload(BaseModel):
    name: str


class DetailedValidationPayload(BaseModel):
    name: str = Field(min_length=3, max_length=5)
    mode: Literal["api"]
    count: int = Field(ge=1, le=3)
    tags: list[str]


def build_exception_test_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)
    register_exception_handlers(app)

    @app.get("/domain-error")
    async def domain_error_route():
        raise NotFoundError(
            "评测记录不存在。", message_key="errors.evaluations.not_found"
        )

    @app.get("/http-error")
    async def http_error_route():
        raise HTTPException(status_code=418, detail="teapot")

    @app.get("/wrapped-http-error")
    async def wrapped_http_error_route():
        raise HTTPException(
            status_code=400,
            detail={"code": 40001, "message": "bad request", "data": {"x": 1}},
        )

    @app.get("/crash")
    async def crash_route():
        raise RuntimeError("boom")

    @app.post("/validation-error")
    async def validation_error_route(_: ValidationPayload):
        return {"ok": True}

    @app.post("/detailed-validation-error")
    async def detailed_validation_error_route(_: DetailedValidationPayload):
        return {"ok": True}

    @app.post("/evaluation-validation-error")
    async def evaluation_validation_error_route(_: EvaluationCreateRequest):
        return {"ok": True}

    return TestClient(app, raise_server_exceptions=False)


def test_loc_to_field_converts_fastapi_locations() -> None:
    assert _loc_to_field(("body", "items", 0, "name")) == "items.0.name"
    assert _loc_to_field(("query", "page")) == "page"
    assert _loc_to_field(("body",)) == "request"


def test_domain_and_http_exceptions_use_wrapped_responses() -> None:
    client = build_exception_test_client()

    domain_response = client.get("/domain-error")
    assert domain_response.status_code == 404
    assert domain_response.json() == {
        "code": 40400,
        "data": None,
        "message": "评测记录不存在。",
    }

    localized_domain_response = client.get(
        "/domain-error", headers={"X-App-Locale": "en-US"}
    )
    assert localized_domain_response.status_code == 404
    assert localized_domain_response.headers["content-language"] == "en-US"
    assert localized_domain_response.headers["vary"] == "X-App-Locale"
    assert localized_domain_response.json() == {
        "code": 40400,
        "data": None,
        "message": "Evaluation record not found.",
    }

    http_response = client.get("/http-error")
    assert http_response.status_code == 418
    assert http_response.json() == {"code": 418, "data": None, "message": "teapot"}

    wrapped_http_response = client.get("/wrapped-http-error")
    assert wrapped_http_response.status_code == 400
    assert wrapped_http_response.json() == {
        "code": 40001,
        "data": {"x": 1},
        "message": "bad request",
    }


def test_unhandled_exceptions_use_internal_error_envelope() -> None:
    client = build_exception_test_client()
    response = client.get("/crash", headers={"X-App-Locale": "en-US"})

    assert response.status_code == 500
    assert response.json() == {
        "code": 50000,
        "data": {"errorType": "RuntimeError"},
        "message": "Internal server error. Please try again later.",
    }


def test_request_validation_errors_are_localized() -> None:
    client = build_exception_test_client()

    response = client.post(
        "/validation-error", json={}, headers={"X-App-Locale": "en-US"}
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == 1000
    assert payload["message"] == "Request parameter validation failed."
    assert payload["data"]["errors"] == [
        {"field": "name", "reason": "This field is required."}
    ]


def test_request_validation_errors_keep_specific_reasons() -> None:
    client = build_exception_test_client()

    response = client.post(
        "/detailed-validation-error",
        json={"name": "ab", "mode": "web", "count": 5, "tags": "tag"},
        headers={"X-App-Locale": "en-US"},
    )

    assert response.status_code == 422
    assert response.json()["data"]["errors"] == [
        {"field": "name", "reason": "Value is too short."},
        {"field": "mode", "reason": "Unsupported value."},
        {"field": "count", "reason": "Value is too large."},
        {"field": "tags", "reason": "Expected a list."},
    ]


def test_unknown_request_validation_reason_uses_localized_generic_message() -> None:
    reason = _validation_reason(
        {"type": "value_error.custom", "msg": "technical validator details"},
        locale="en-US",
    )

    assert reason == "Invalid value."


def test_custom_request_validation_error_uses_stable_translation() -> None:
    client = build_exception_test_client()

    response = client.post(
        "/evaluation-validation-error",
        json={
            "requestId": "req_123456",
            "submitMethod": "api",
            "agentId": "agt_demo",
            "datasetIds": ["A1_identity_leakage"],
            "parameters": {
                "difficulty": 0.5,
                "timeoutMinutes": 15,
                "maxSteps": 30,
            },
            "publicToLeaderboard": False,
            "leaderboardDisplayMode": "public",
        },
        headers={"X-App-Locale": "en-US"},
    )

    assert response.status_code == 422
    assert response.json()["data"]["errors"] == [
        {
            "field": "request",
            "reason": "publicToLeaderboard=false is deprecated. Use leaderboardDisplayMode=anonymous instead.",
        }
    ]
