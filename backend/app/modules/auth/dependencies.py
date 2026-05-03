"""认证域依赖。"""

from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.repository import AuthRepository
from app.platform.auth import get_db
from app.platform.errors import AuthError
from app.platform.security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """解析访问令牌并返回当前登录用户。"""
    if credentials is None or not credentials.credentials:
        raise AuthError()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except Exception as exc:  # pragma: no cover - defensive parsing
        raise AuthError() from exc

    repository = AuthRepository(db)
    user = await repository.get_user_by_id(user_id)
    if user is None:
        raise AuthError()
    return user
