from typing import AsyncGenerator
from fastapi import Depends
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.response import fail, unauthorized
from app.core.security import decode_access_token
from app.crud import get_user_by_id
from app.db.session import AsyncSessionLocal
from app.models.user import User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise unauthorized("未授权，请先登录")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except Exception:
        raise unauthorized()

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise unauthorized()

    return user


async def get_current_platform_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise fail(status.HTTP_401_UNAUTHORIZED, 40100, "未登录或登录已失效。")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except Exception:
        raise fail(status.HTTP_401_UNAUTHORIZED, 40100, "未登录或登录已失效。")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise fail(status.HTTP_401_UNAUTHORIZED, 40100, "未登录或登录已失效。")

    return user
