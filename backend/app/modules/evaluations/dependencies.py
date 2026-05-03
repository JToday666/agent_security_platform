"""FastAPI dependency factories for evaluation routes."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluations.repository import EvaluationRepository
from app.modules.evaluations.service import EvaluationService
from app.platform.auth import get_db


def get_evaluation_service(db: AsyncSession = Depends(get_db)) -> EvaluationService:
    """Return the evaluation service for route handlers."""
    return EvaluationService(EvaluationRepository(db))

