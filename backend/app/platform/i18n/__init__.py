"""Backend locale parsing, request context and message catalog utilities."""

from __future__ import annotations

import json
import logging
import re
from contextvars import ContextVar, Token
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from string import Formatter
from typing import Any, Mapping

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

LOGGER = logging.getLogger(__name__)

SUPPORTED_LOCALES = ("zh-CN", "en-US", "fr-FR", "es-ES", "ja-JP")
DEFAULT_LOCALE = "zh-CN"
LOCALE_VARY_HEADER = "X-App-Locale"
MAX_LANGUAGE_HEADER_LENGTH = 256

_LOCALE_ALIASES: dict[str, str] = {
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh-hans": "zh-CN",
    "zh-hans-cn": "zh-CN",
    "en": "en-US",
    "en-us": "en-US",
    "en-gb": "en-US",
    "fr": "fr-FR",
    "fr-fr": "fr-FR",
    "fr-ca": "fr-FR",
    "es": "es-ES",
    "es-es": "es-ES",
    "es-mx": "es-ES",
    "ja": "ja-JP",
    "ja-jp": "ja-JP",
}
_LOCALE_PATTERN = re.compile(r"^[a-zA-Z]{1,8}(?:[-_][a-zA-Z0-9]{1,8})*$")
_current_locale: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)


@dataclass(slots=True)
class LocaleToken:
    """Small wrapper that exposes a reset method for locale context tokens."""

    token: Token[str]

    def reset(self) -> None:
        _current_locale.reset(self.token)


class SafeFormatDict(dict[str, Any]):
    """Keep unknown format placeholders visible instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def normalize_locale(locale: str | None) -> str:
    """Normalize a user-provided locale into the supported locale set."""
    if not locale:
        return DEFAULT_LOCALE
    candidate = locale.strip().replace("_", "-")
    if len(candidate) > MAX_LANGUAGE_HEADER_LENGTH or not _LOCALE_PATTERN.match(
        candidate
    ):
        return DEFAULT_LOCALE
    return _LOCALE_ALIASES.get(candidate.lower(), DEFAULT_LOCALE)


def resolve_locale(app_locale: str | None, accept_language: str | None = None) -> str:
    """Resolve content locale from the canonical app locale header only."""
    _ = accept_language
    return normalize_locale(app_locale)


def set_current_locale(locale: str) -> LocaleToken:
    """Set the current request locale and return a resettable token."""
    return LocaleToken(_current_locale.set(normalize_locale(locale)))


def get_current_locale() -> str:
    """Return the current request locale, defaulting to zh-CN."""
    return _current_locale.get()


@lru_cache(maxsize=len(SUPPORTED_LOCALES))
def _load_catalog(locale: str) -> dict[str, str]:
    path = Path(__file__).resolve().parent / "messages" / f"{locale}.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return {
        str(key): str(value) for key, value in payload.items() if isinstance(value, str)
    }


def _format_message(template: str, params: Mapping[str, Any] | None) -> str:
    if not params:
        return template
    safe_params = SafeFormatDict(params)
    try:
        return template.format_map(safe_params)
    except ValueError:
        fields = {
            field_name
            for _, field_name, _, _ in Formatter().parse(template)
            if field_name
        }
        LOGGER.warning(
            "Invalid i18n template placeholders", extra={"fields": sorted(fields)}
        )
        return template


def translate(
    key: str,
    params: Mapping[str, Any] | None = None,
    *,
    locale: str | None = None,
    default: str | None = None,
) -> str:
    """Translate a stable message key with fallback to zh-CN, default, then key."""
    resolved_locale = normalize_locale(locale or get_current_locale())
    template = _load_catalog(resolved_locale).get(key)
    if template is None and resolved_locale != DEFAULT_LOCALE:
        template = _load_catalog(DEFAULT_LOCALE).get(key)
    if template is None:
        LOGGER.warning(
            "Missing i18n message", extra={"locale": resolved_locale, "key": key}
        )
        template = default if default is not None else key
    return _format_message(template, params)


def localize_message(
    message: str,
    *,
    key: str | None = None,
    params: Mapping[str, Any] | None = None,
    locale: str | None = None,
) -> str:
    """Translate a structured key, or return the original message as fallback."""
    if key:
        return translate(key, params, locale=locale, default=message)
    return message


def add_locale_headers(response: Response, locale: str | None = None) -> None:
    """Attach normalized content-language and cache vary headers."""
    resolved_locale = normalize_locale(locale or get_current_locale())
    response.headers["Content-Language"] = resolved_locale
    existing_vary = response.headers.get("Vary")
    if not existing_vary:
        response.headers["Vary"] = LOCALE_VARY_HEADER
        return
    vary_values = [value.strip() for value in existing_vary.split(",") if value.strip()]
    if not any(value.lower() == LOCALE_VARY_HEADER.lower() for value in vary_values):
        response.headers["Vary"] = f"{existing_vary}, {LOCALE_VARY_HEADER}"


def is_json_response(response: Response) -> bool:
    """Return whether the response body is JSON and should vary by locale."""
    content_type = (
        response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    )
    return content_type == "application/json" or content_type.endswith("+json")


class LocaleMiddleware(BaseHTTPMiddleware):
    """Resolve request locale once and expose it through ContextVar."""

    async def dispatch(self, request: Request, call_next):
        locale = resolve_locale(request.headers.get("X-App-Locale"))
        request.state.locale = locale
        token = set_current_locale(locale)
        try:
            response = await call_next(request)
        finally:
            token.reset()
        if is_json_response(response):
            add_locale_headers(response, locale)
        return response
