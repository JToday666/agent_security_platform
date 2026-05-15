"""Agent module data access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent


class AgentRepository:
    """Persist and query registered Agents."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, agent: Agent) -> Agent:
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def list_for_user(
        self, user_id: int, *, include_archived: bool, status: str | None
    ) -> list[Agent]:
        stmt = select(Agent).where(Agent.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(Agent.status != "archived")
        if status:
            stmt = stmt.where(Agent.status == status)
        stmt = stmt.order_by(Agent.created_at.desc(), Agent.id.desc())
        return list((await self.db.execute(stmt)).scalars())

    async def get_by_public_id(self, public_id: str) -> Agent | None:
        return (
            await self.db.execute(select(Agent).where(Agent.public_id == public_id))
        ).scalar_one_or_none()

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def refresh(self, entity) -> None:
        await self.db.refresh(entity)
