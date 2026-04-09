"""认证依赖，负责提供数据库会话与当前用户。"""

from typing import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.repository import AuthRepository
from app.shared.db.session import AsyncSessionLocal
from app.shared.errors import AuthError
from app.shared.security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """提供请求级异步数据库会话。"""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
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
