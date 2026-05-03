"""评分接口路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import get_current_user
from app.modules.scoring.schemas import EvaluationScoreResponse, ScoreRecalculateRequest
from app.modules.scoring.service import ScoringService
from app.platform.auth import get_db
from app.platform.http import success_payload
from app.platform.schemas import Envelope

router = APIRouter(prefix="/evaluations", tags=["scoring"])


def get_scoring_service(db: AsyncSession = Depends(get_db)) -> ScoringService:
    return ScoringService(db)


@router.get("/{evaluationId}/score", response_model=Envelope[EvaluationScoreResponse])
async def get_evaluation_score(
    evaluationId: str,
    current_user=Depends(get_current_user),
    service: ScoringService = Depends(get_scoring_service),
):
    response = await service.get_score(evaluationId, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.post("/{evaluationId}/score/recalculate", response_model=Envelope[EvaluationScoreResponse])
async def recalculate_evaluation_score(
    evaluationId: str,
    payload: ScoreRecalculateRequest,
    current_user=Depends(get_current_user),
    service: ScoringService = Depends(get_scoring_service),
):
    response = await service.recalculate_score(
        evaluationId,
        current_user,
        score_model_version=payload.score_model_version,
        benchmark_version=payload.benchmark_version,
    )
    return success_payload(response.model_dump(by_alias=True))
