from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(word.capitalize() for word in tail)


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    code: int
    data: T | None = None
    message: str = "success"


class MessagePayload(CamelModel):
    message: str


class ValidationErrorItem(CamelModel):
    field: str
    reason: str


class ValidationErrorData(CamelModel):
    errors: list[ValidationErrorItem] = Field(default_factory=list)
