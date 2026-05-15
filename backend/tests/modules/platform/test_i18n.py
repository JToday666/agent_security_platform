from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from fastapi.testclient import TestClient

from app.platform.i18n import (
    DEFAULT_LOCALE,
    LocaleMiddleware,
    get_current_locale,
    normalize_locale,
    resolve_locale,
    set_current_locale,
    translate,
)


def test_normalize_locale_accepts_supported_aliases() -> None:
    assert normalize_locale("zh") == "zh-CN"
    assert normalize_locale("zh-Hans-CN") == "zh-CN"
    assert normalize_locale("en-GB") == "en-US"
    assert normalize_locale("fr-CA") == "fr-FR"
    assert normalize_locale("es-MX") == "es-ES"
    assert normalize_locale("ja") == "ja-JP"
    assert normalize_locale("de-DE") == DEFAULT_LOCALE


def test_resolve_locale_uses_only_app_locale_header() -> None:
    assert resolve_locale("en-US", "ja-JP") == "en-US"
    assert resolve_locale("de-DE", "ja-JP") == DEFAULT_LOCALE
    assert resolve_locale(None, "ja-JP") == DEFAULT_LOCALE
    assert resolve_locale(None, "de-DE;q=1, ja-JP;q=0.8, en-US;q=0.4") == DEFAULT_LOCALE


def test_current_locale_context_resets_to_default() -> None:
    token = set_current_locale("en-US")
    try:
        assert get_current_locale() == "en-US"
    finally:
        token.reset()

    assert get_current_locale() == DEFAULT_LOCALE


def test_translate_uses_locale_fallback_and_interpolation() -> None:
    assert (
        translate("errors.auth.invalid_credentials", locale="en-US")
        == "Incorrect username or password."
    )
    assert (
        translate("errors.auth.invalid_credentials", locale="zh-CN")
        == "用户名或密码错误"
    )
    assert (
        translate(
            "evaluations.status.running_dataset", {"datasetName": "A1"}, locale="en-US"
        )
        == "Currently evaluating dataset A1."
    )
    assert translate("unknown.key", locale="en-US", default="fallback") == "fallback"


def test_locale_middleware_adds_headers_only_to_json_responses() -> None:
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)

    @app.get("/json")
    async def json_route():
        return JSONResponse({"ok": True}, headers={"Vary": "Origin"})

    @app.get("/text")
    async def text_route():
        return Response("ok", media_type="text/plain")

    client = TestClient(app)

    json_response = client.get("/json", headers={"X-App-Locale": "en-US"})
    assert json_response.headers["content-language"] == "en-US"
    assert json_response.headers["vary"] == "Origin, X-App-Locale"

    text_response = client.get("/text", headers={"X-App-Locale": "en-US"})
    assert "content-language" not in text_response.headers
    assert "vary" not in text_response.headers
