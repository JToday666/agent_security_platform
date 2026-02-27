from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.response import unauthorized
from app.core.security import decode_access_token
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

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise unauthorized()

    return user
