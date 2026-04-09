from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
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
        await self.db.commit()
        await self.db.refresh(user)
        return user
