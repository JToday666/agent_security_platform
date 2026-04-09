from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluations.repository import EvaluationRepository
from app.modules.evaluations.schemas import EvaluationActionRequest, EvaluationDetail, EvaluationListItem
from app.modules.evaluations.service import EvaluationService
from app.shared.auth import get_current_user, get_db
from app.shared.http import success_payload
from app.shared.schemas import Envelope

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def get_evaluation_service(db: AsyncSession = Depends(get_db)) -> EvaluationService:
    return EvaluationService(EvaluationRepository(db))


@router.get("", response_model=Envelope[list[EvaluationListItem]])
async def list_evaluations(current_user=Depends(get_current_user), service: EvaluationService = Depends(get_evaluation_service)):
    response = await service.list_evaluations(current_user=current_user)
    return success_payload([item.model_dump(by_alias=True) for item in response])


@router.get("/{evaluationId}", response_model=Envelope[EvaluationDetail])
async def get_evaluation_detail(
    evaluationId: str,
    current_user=Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    response = await service.get_evaluation_detail(evaluationId, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.post("/{evaluationId}/actions", response_model=Envelope[EvaluationDetail])
async def apply_evaluation_action(
    evaluationId: str,
    payload: EvaluationActionRequest,
    current_user=Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    response = await service.apply_action(evaluationId, payload, current_user)
    return success_payload(response.model_dump(by_alias=True))
