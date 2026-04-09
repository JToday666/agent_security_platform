from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.shared.errors import DomainError, ValidationDomainError
from app.shared.http import build_validation_error_data, json_error_response


def _loc_to_field(loc: tuple[Any, ...]) -> str:
    parts = [str(item) for item in loc if item not in {"body", "query", "path"}]
    return ".".join(parts) if parts else "request"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError):
        return json_error_response(
            http_status=exc.http_status,
            code=exc.code,
            message=exc.message,
            data=exc.data,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(_: Request, exc: RequestValidationError):
        payload = build_validation_error_data(
            [
                {
                    "field": _loc_to_field(tuple(error["loc"])),
                    "reason": error["msg"],
                }
                for error in exc.errors()
            ]
        ).model_dump(by_alias=True)
        validation_error = ValidationDomainError("请求参数校验失败", data=payload)
        return json_error_response(
            http_status=validation_error.http_status,
            code=validation_error.code,
            message=validation_error.message,
            data=validation_error.data,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and {"code", "message", "data"}.issubset(detail.keys()):
            return json_error_response(
                http_status=exc.status_code,
                code=detail["code"],
                message=detail["message"],
                data=detail.get("data"),
            )
        return json_error_response(
            http_status=exc.status_code,
            code=exc.status_code,
            message=str(detail),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception):  # pragma: no cover - safety net
        return json_error_response(
            http_status=500,
            code=50000,
            message="服务内部错误，请稍后重试。",
            data={"errorType": exc.__class__.__name__},
        )
