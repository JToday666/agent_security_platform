from __future__ import annotations

import json
import re
from pathlib import Path

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


CATALOG_DIR = Path(__file__).resolve().parents[3] / "app" / "platform" / "i18n" / "messages"
PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z0-9_]+)\}")
FRENCH_ASCII_ACCENT_WORDS = re.compile(
    r"\b(?:etre|etes|ete|acces|succes|verification|verifies|Reessayez|tache|"
    r"resultat|execution|donnees|difficulte|deja|enregistre|parametres|"
    r"depasser|depassent|criteres|Selectionnez|evaluation|echantillon|"
    r"echantillons|televerser|echoue|echeance|apres|creee|demarrer|arret|"
    r"generera|methode|modifie|refuse|connecte|expire|retourne)\b",
    re.IGNORECASE,
)
SPANISH_ASCII_ACCENT_WORDS = re.compile(
    r"\b(?:vacio|vacios|devolvio|Intentalo|envian|despues|ejecucion|"
    r"contrasena|sesion|codigo|version|evaluacion|parametros|aparecera|"
    r"clasificacion|publica|Asegurate|descripcion|informacion|accion|metodo|"
    r"puntuacion|recalculo|anonimo|envio|Asincrono|valido|terminara|"
    r"generara|mas|tambien|reanudala|pausara)\b",
    re.IGNORECASE,
)


def load_catalog(locale: str) -> dict[str, str]:
    return json.loads((CATALOG_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def placeholders(value: str) -> set[str]:
    return set(PLACEHOLDER_PATTERN.findall(value))


def test_backend_catalog_keys_and_placeholders_are_aligned() -> None:
    source_catalog = load_catalog("zh-CN")
    source_keys = set(source_catalog)

    for locale_path in CATALOG_DIR.glob("*.json"):
        catalog = load_catalog(locale_path.stem)
        assert set(catalog) == source_keys
        for key, source_value in source_catalog.items():
            assert placeholders(catalog[key]) == placeholders(source_value)


def test_french_and_spanish_backend_catalogs_use_standard_orthography() -> None:
    french_hits = {
        key: FRENCH_ASCII_ACCENT_WORDS.findall(value)
        for key, value in load_catalog("fr-FR").items()
        if FRENCH_ASCII_ACCENT_WORDS.search(value)
    }
    spanish_hits = {
        key: SPANISH_ASCII_ACCENT_WORDS.findall(value)
        for key, value in load_catalog("es-ES").items()
        if SPANISH_ASCII_ACCENT_WORDS.search(value)
    }

    assert french_hits == {}
    assert spanish_hits == {}


def test_japanese_backend_catalog_preserves_do_not_translate_terms() -> None:
    catalog_text = "\n".join(load_catalog("ja-JP").values())

    assert "Agent" in catalog_text
    assert "エージェント" not in catalog_text


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
