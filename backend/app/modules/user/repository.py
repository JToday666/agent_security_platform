"""用户模块数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """封装用户资料相关的数据库操作。"""

    def __init__(self, db: AsyncSession) -> None:
        """绑定用户资料管理链路共用的异步数据库会话。"""
        self.db = db

    async def is_username_taken(
        self, username: str, exclude_user_id: int | None = None
    ) -> bool:
        """判断用户名是否已被其他用户占用。"""
        stmt = select(User).where(User.username == username)
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def save_user(self, user: User) -> User:
        """写入用户资料变更并返回当前实体。"""
        self.db.add(user)
        await self.db.flush()
        return user

    async def commit(self) -> None:
        """提交用户资料相关事务。"""
        await self.db.commit()

    async def rollback(self) -> None:
        """回滚用户资料相关事务。"""
        await self.db.rollback()

    async def refresh(self, entity) -> None:
        """刷新指定实体的数据库状态。"""
        await self.db.refresh(entity)
