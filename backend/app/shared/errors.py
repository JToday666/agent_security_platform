"""项目内统一使用的领域异常定义。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DomainError(Exception):
    """业务异常的基础类型。"""

    http_status: int
    code: int
    message: str
    data: Any = None

    def __str__(self) -> str:
        return self.message


class ValidationDomainError(DomainError):
    """表示请求参数或业务校验失败。"""

    def __init__(self, message: str, data: Any = None, http_status: int = 422, code: int = 1000) -> None:
        super().__init__(http_status=http_status, code=code, message=message, data=data)


class AuthError(DomainError):
    """表示认证失败或登录状态失效。"""

    def __init__(self, message: str = "未登录或登录已失效。", code: int = 40100) -> None:
        super().__init__(http_status=401, code=code, message=message, data=None)


class ForbiddenError(DomainError):
    """表示当前用户无权执行指定操作。"""

    def __init__(self, message: str, code: int = 40300, data: Any = None) -> None:
        super().__init__(http_status=403, code=code, message=message, data=data)


class NotFoundError(DomainError):
    """表示请求的业务对象不存在。"""

    def __init__(self, message: str, code: int = 40400, data: Any = None) -> None:
        super().__init__(http_status=404, code=code, message=message, data=data)


class ConflictError(DomainError):
    """表示请求与当前资源状态冲突。"""

    def __init__(self, message: str, code: int = 40900, data: Any = None) -> None:
        super().__init__(http_status=409, code=code, message=message, data=data)
