"""统一封装接口响应体相关工具函数。"""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from app.shared.schemas import Envelope, ValidationErrorData, ValidationErrorItem


def success_payload(data: Any = None, message: str = "success") -> dict[str, Any]:
    """构造成功响应的 envelope 数据。"""
    return Envelope[Any](code=0, data=data, message=message).model_dump(by_alias=True)


def error_payload(code: int, message: str, data: Any = None) -> dict[str, Any]:
    """构造错误响应的 envelope 数据。"""
    return Envelope[Any](code=code, data=data, message=message).model_dump(by_alias=True)


def json_error_response(http_status: int, code: int, message: str, data: Any = None) -> JSONResponse:
    """返回符合统一结构的 JSON 错误响应。"""
    return JSONResponse(status_code=http_status, content=error_payload(code=code, message=message, data=data))


def build_validation_error_data(errors: list[dict[str, str]]) -> ValidationErrorData:
    """整理参数校验错误的返回数据。"""
    return ValidationErrorData(
        errors=[ValidationErrorItem(field=item["field"], reason=item["reason"]) for item in errors]
    )
