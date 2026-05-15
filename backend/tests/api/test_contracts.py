from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.api import api_router


def test_v1_router_registers_business_routes() -> None:
    route_paths = {route.path for route in api_router.routes}

    assert "/v1/datasets/catalog" in route_paths
    assert "/v1/datasets/{datasetId}" in route_paths
    assert "/v1/agents/templates" in route_paths
    assert "/v1/agents" in route_paths
    assert "/v1/agents/{agentId}" in route_paths
    assert "/v1/agents/{agentId}/verify" in route_paths
    assert "/v1/agents/{agentId}/archive" in route_paths
    assert "/v1/evaluations/meta" in route_paths
    assert "/v1/evaluations/validate" in route_paths
    assert "/v1/evaluations" in route_paths
    assert "/v1/evaluations/{evaluationId}" in route_paths
    assert "/v1/evaluations/{evaluationId}/actions" in route_paths
    assert "/v1/agents/submit-meta" not in route_paths
    assert "/v1/agents/precheck" not in route_paths
    assert "/v1/agents/submit" not in route_paths


def test_root_and_meta_routes_return_envelope(client: TestClient) -> None:
    for path in ["/", "/api/", "/api/v1/"]:
        response = client.get(path)

        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 0
        assert payload["message"] == "success"
        assert isinstance(payload["data"], dict)
        assert "message" in payload["data"]


def test_locale_headers_are_normalized_on_json_responses(client: TestClient) -> None:
    preferred_response = client.get(
        "/",
        headers={"X-App-Locale": "en-US", "Accept-Language": "ja-JP"},
    )

    assert preferred_response.status_code == 200
    assert preferred_response.headers["content-language"] == "en-US"
    assert preferred_response.headers["vary"] == "X-App-Locale"

    unsupported_response = client.get(
        "/",
        headers={"X-App-Locale": "de-DE", "Accept-Language": "ja-JP"},
    )

    assert unsupported_response.status_code == 200
    assert unsupported_response.headers["content-language"] == "zh-CN"
    assert unsupported_response.headers["vary"] == "X-App-Locale"

    accept_language_only_response = client.get(
        "/",
        headers={"Accept-Language": "de-DE;q=1, ja-JP;q=0.8, en-US;q=0.4"},
    )

    assert accept_language_only_response.status_code == 200
    assert accept_language_only_response.headers["content-language"] == "zh-CN"
    assert accept_language_only_response.headers["vary"] == "X-App-Locale"


def test_request_validation_errors_use_envelope_shape(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "demo-user",
            "email": "invalid-email",
            "password": "secret123",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == 1000
    assert payload["message"] == "请求参数校验失败"
    assert "errors" in payload["data"]
    assert payload["data"]["errors"][0]["field"] == "email"


def test_unauthorized_profile_request_returns_wrapped_response(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/user/profile")

    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == 40100
    assert payload["message"] == "未登录或登录已失效。"
    assert payload["data"] is None
