"""共享基础能力的统一导出。"""

from app.shared.config import settings
from app.shared.errors import (
    AuthError,
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    ValidationDomainError,
)

__all__ = [
    "AuthError",
    "ConflictError",
    "DomainError",
    "ForbiddenError",
    "NotFoundError",
    "ValidationDomainError",
    "settings",
]
