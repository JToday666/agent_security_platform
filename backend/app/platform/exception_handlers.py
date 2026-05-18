"""注册全局异常处理器并统一返回响应结构。"""

from __future__ import annotations

from typing import Any, TypedDict, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.platform.errors import DomainError, ValidationDomainError
from app.platform.http import build_validation_error_data, json_error_response
from app.platform.i18n import localize_message, translate


class _HttpEnvelopeBaseDetail(TypedDict):
    code: int
    message: Any
    data: Any


class _HttpEnvelopeDetail(_HttpEnvelopeBaseDetail, total=False):
    messageKey: str
    messageParams: dict[str, Any]


def _loc_to_field(loc: tuple[Any, ...]) -> str:
    """把 FastAPI 校验错误定位信息转换为字段路径。"""
    parts = [str(item) for item in loc if item not in {"body", "query", "path"}]
    return ".".join(parts) if parts else "request"


def _request_locale(request: Request) -> str | None:
    """Read normalized locale captured by LocaleMiddleware."""
    return getattr(request.state, "locale", None)


_VALIDATION_REASON_KEYS: dict[str, str] = {
    "missing": "validation.field.required",
    "string_too_short": "validation.field.too_short",
    "string_too_long": "validation.field.too_long",
    "too_short": "validation.field.too_short",
    "too_long": "validation.field.too_long",
    "greater_than": "validation.field.too_small",
    "greater_than_equal": "validation.field.too_small",
    "less_than": "validation.field.too_large",
    "less_than_equal": "validation.field.too_large",
    "literal_error": "validation.field.unsupported",
    "enum": "validation.field.unsupported",
    "list_type": "validation.field.expected_list",
    "dict_type": "validation.field.expected_object",
    "string_type": "validation.field.expected_string",
    "int_type": "validation.field.expected_integer",
    "int_parsing": "validation.field.expected_integer",
    "float_type": "validation.field.expected_number",
    "float_parsing": "validation.field.expected_number",
    "finite_number": "validation.field.expected_number",
    "bool_type": "validation.field.expected_boolean",
    "bool_parsing": "validation.field.expected_boolean",
    "public_leaderboard_deprecated": (
        "validation.evaluations.public_leaderboard_deprecated"
    ),
}


def _validation_reason(error: dict[str, Any], *, locale: str | None = None) -> str:
    """Translate a FastAPI/Pydantic validation error reason."""
    error_type = str(error.get("type") or "")
    message_key = _VALIDATION_REASON_KEYS.get(error_type)
    if message_key is not None:
        return translate(message_key, locale=locale)
    return translate("validation.field.invalid", locale=locale)


def _domain_error_message(exc: DomainError, *, locale: str | None = None) -> str:
    """Return the localized message for a structured domain error."""
    return localize_message(
        exc.message,
        key=exc.message_key,
        params=exc.message_params,
        locale=locale,
    )


def _structured_http_detail(detail: Any) -> _HttpEnvelopeDetail | None:
    """Return a typed HTTPException detail when it matches the platform envelope."""
    if not isinstance(detail, dict) or not {"code", "message", "data"}.issubset(
        detail.keys()
    ):
        return None
    if not isinstance(detail.get("code"), int):
        return None
    return cast(_HttpEnvelopeDetail, detail)


def register_exception_handlers(app: FastAPI) -> None:
    """为应用挂载统一的异常响应处理器。"""

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        """处理业务异常并返回统一 envelope 响应。"""
        locale = _request_locale(request)
        return json_error_response(
            http_status=exc.http_status,
            code=exc.code,
            message=_domain_error_message(exc, locale=locale),
            data=exc.data,
            locale=locale,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        """处理请求参数校验错误并转换为统一业务错误结构。"""
        locale = _request_locale(request)
        payload = build_validation_error_data(
            [
                {
                    "field": _loc_to_field(tuple(error["loc"])),
                    "reason": _validation_reason(error, locale=locale),
                }
                for error in exc.errors()
            ]
        ).model_dump(by_alias=True)
        validation_error = ValidationDomainError(
            "请求参数校验失败", data=payload, message_key="errors.validation.request"
        )
        return json_error_response(
            http_status=validation_error.http_status,
            code=validation_error.code,
            message=_domain_error_message(validation_error, locale=locale),
            data=validation_error.data,
            locale=locale,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理 FastAPI 原生 HTTP 异常并对齐返回结构。"""
        locale = _request_locale(request)
        detail = exc.detail
        structured_detail = _structured_http_detail(detail)
        if structured_detail is not None:
            message_key = structured_detail.get("messageKey")
            message = localize_message(
                str(structured_detail["message"]),
                key=message_key if isinstance(message_key, str) else None,
                params=(
                    structured_detail.get("messageParams")
                    if isinstance(structured_detail.get("messageParams"), dict)
                    else None
                ),
                locale=locale,
            )
            return json_error_response(
                http_status=exc.status_code,
                code=structured_detail["code"],
                message=message,
                data=structured_detail.get("data"),
                locale=locale,
            )
        return json_error_response(
            http_status=exc.status_code,
            code=exc.status_code,
            message=localize_message(str(detail), locale=locale),
            locale=locale,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ):  # pragma: no cover - safety net
        """兜底处理未捕获异常，供应用入口统一注册调用。"""
        locale = _request_locale(request)
        return json_error_response(
            http_status=500,
            code=50000,
            message=translate("errors.common.internal", locale=locale),
            data={"errorType": exc.__class__.__name__},
            locale=locale,
        )
