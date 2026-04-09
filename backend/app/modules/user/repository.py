"""用户模块数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """封装用户资料相关的数据库操作。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def is_username_taken(self, username: str, exclude_user_id: int | None = None) -> bool:
        stmt = select(User).where(User.username == username)
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def save_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def refresh(self, entity) -> None:
        await self.db.refresh(entity)
