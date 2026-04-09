"""共享认证基础依赖。"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.db.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """提供请求级异步数据库会话。"""
    async with AsyncSessionLocal() as session:
        yield session
