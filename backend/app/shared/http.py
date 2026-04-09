from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from app.shared.schemas import Envelope, ValidationErrorData, ValidationErrorItem


def success_payload(data: Any = None, message: str = "success") -> dict[str, Any]:
    return Envelope[Any](code=0, data=data, message=message).model_dump(by_alias=True)


def error_payload(code: int, message: str, data: Any = None) -> dict[str, Any]:
    return Envelope[Any](code=code, data=data, message=message).model_dump(by_alias=True)


def json_error_response(http_status: int, code: int, message: str, data: Any = None) -> JSONResponse:
    return JSONResponse(status_code=http_status, content=error_payload(code=code, message=message, data=data))


def build_validation_error_data(errors: list[dict[str, str]]) -> ValidationErrorData:
    return ValidationErrorData(
        errors=[ValidationErrorItem(field=item["field"], reason=item["reason"]) for item in errors]
    )
