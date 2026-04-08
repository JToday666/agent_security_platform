from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_platform_user, get_db
from app.api.response import fail, success
from app.models.user import User
from app.schemas.evaluations import EvaluationActionRequest
from app.services.evaluations import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def get_evaluation_service(db: AsyncSession = Depends(get_db)) -> EvaluationService:
    return EvaluationService(db)


@router.get("")
async def list_evaluations(
    current_user: User = Depends(get_current_platform_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    try:
        return success(data=await service.list_evaluations(current_user=current_user))
    except HTTPException:
        raise
    except Exception:
        raise fail(status.HTTP_500_INTERNAL_SERVER_ERROR, 50000, "评测记录加载失败。")


@router.get("/{evaluationId}")
async def get_evaluation_detail(
    evaluationId: str,
    current_user: User = Depends(get_current_platform_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    try:
        return success(
            data=await service.get_evaluation_detail(
                evaluation_id=evaluationId,
                current_user=current_user,
            )
        )
    except HTTPException:
        raise
    except Exception:
        raise fail(status.HTTP_500_INTERNAL_SERVER_ERROR, 50000, "评测详情加载失败，请稍后重试。")


@router.post("/{evaluationId}/actions")
async def apply_evaluation_action(
    evaluationId: str,
    payload: EvaluationActionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_platform_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    try:
        return success(
            data=await service.apply_action(
                evaluation_id=evaluationId,
                payload=payload,
                current_user=current_user,
                background_tasks=background_tasks,
            )
        )
    except HTTPException:
        raise
    except Exception:
        raise fail(status.HTTP_500_INTERNAL_SERVER_ERROR, 50000, "任务操作失败，请稍后重试。")
