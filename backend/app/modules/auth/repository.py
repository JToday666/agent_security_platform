from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_login_identifier(self, identifier: str) -> User | None:
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
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none() is not None

    async def is_email_taken(self, email: str) -> bool:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def create_user(self, username: str, email: str, hashed_password: str) -> User:
        user = User(username=username, email=email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.flush()
        return user

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def refresh(self, entity) -> None:
        await self.db.refresh(entity)
