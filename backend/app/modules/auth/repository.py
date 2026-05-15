"""认证模块数据访问层。"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class AuthRepository:
    """封装认证流程使用的用户查询与持久化操作。"""

    def __init__(self, db: AsyncSession) -> None:
        """绑定认证流程共用的异步数据库会话。"""
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User | None:
        """按用户主键查询账号记录，供鉴权依赖和服务层复用。"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """按用户名查询账号记录。"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """按邮箱查询账号记录。"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_login_identifier(self, identifier: str) -> User | None:
        """按登录标识查询账号，支持用户名或邮箱两种输入。"""
        normalized_identifier = identifier.strip()
        result = await self.db.execute(
            select(User).where(
                or_(
                    User.username == normalized_identifier,
                    User.email == normalized_identifier.lower(),
                )
            )
        )
        return result.scalar_one_or_none()

    async def is_username_taken(self, username: str) -> bool:
        """判断用户名是否已被占用。"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none() is not None

    async def is_email_taken(self, email: str) -> bool:
        """判断邮箱是否已被占用。"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def create_user(
        self, username: str, email: str, hashed_password: str
    ) -> User:
        """创建新用户记录，供认证服务在注册流程中调用。"""
        user = User(username=username, email=email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.flush()
        return user

    async def commit(self) -> None:
        """提交当前认证相关事务。"""
        await self.db.commit()

    async def rollback(self) -> None:
        """回滚当前认证相关事务。"""
        await self.db.rollback()

    async def refresh(self, entity) -> None:
        """刷新指定实体的最新数据库状态。"""
        await self.db.refresh(entity)
