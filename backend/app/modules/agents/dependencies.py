"""FastAPI dependency factories for the Agent module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agents.repository import AgentRepository
from app.modules.agents.service import AgentService
from app.platform.auth import get_db


def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    """Return the Agent service for route handlers."""
    return AgentService(AgentRepository(db))

