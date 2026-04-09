"""通用响应结构和基础 Pydantic 模型。"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    """将蛇形命名转换为驼峰命名。"""
    head, *tail = value.split("_")
    return head + "".join(word.capitalize() for word in tail)


class CamelModel(BaseModel):
    """默认使用驼峰别名的基础模型。"""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """统一接口响应外层结构。"""

    code: int
    data: T | None = None
    message: str = "success"


class MessagePayload(CamelModel):
    """仅包含提示消息的响应体。"""

    message: str


class ValidationErrorItem(CamelModel):
    """单个字段校验错误项。"""

    field: str
    reason: str


class ValidationErrorData(CamelModel):
    """参数校验错误集合。"""

    errors: list[ValidationErrorItem] = Field(default_factory=list)
