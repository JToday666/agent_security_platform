"""评测任务模块路由，负责任务查询与动作接口。"""

from fastapi import APIRouter, Depends

from app.modules.evaluations.dependencies import get_evaluation_service
from app.modules.evaluations.schemas import (
    EvaluationActionRequest,
    EvaluationCreateRequest,
    EvaluationCreateResponse,
    EvaluationDetail,
    EvaluationListItem,
    EvaluationSubmitMeta,
    EvaluationValidateResponse,
)
from app.modules.evaluations.service import EvaluationService
from app.modules.auth.dependencies import get_current_user
from app.platform.http import success_payload
from app.platform.schemas import Envelope

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("", response_model=Envelope[list[EvaluationListItem]])
async def list_evaluations(
    current_user=Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """返回当前用户的评测任务列表。"""
    response = await service.list_evaluations(current_user=current_user)
    return success_payload([item.model_dump(by_alias=True) for item in response])


@router.get("/meta", response_model=Envelope[EvaluationSubmitMeta])
async def evaluation_submit_meta(
    service: EvaluationService = Depends(get_evaluation_service),
):
    """返回评测提交页元数据。"""
    response = await service.get_submit_meta()
    return success_payload(response.model_dump(by_alias=True))


@router.post("/validate", response_model=Envelope[EvaluationValidateResponse])
async def validate_evaluation_submission(
    payload: EvaluationCreateRequest,
    current_user=Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """校验评测提交请求。"""
    response = await service.validate_submission(payload, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.post("", response_model=Envelope[EvaluationCreateResponse])
async def create_evaluation(
    payload: EvaluationCreateRequest,
    current_user=Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """创建评测任务。"""
    response = await service.create_evaluation(payload, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.get("/{evaluationId}", response_model=Envelope[EvaluationDetail])
async def get_evaluation_detail(
    evaluationId: str,
    current_user=Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """返回指定评测任务详情。"""
    response = await service.get_evaluation_detail(evaluationId, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.post("/{evaluationId}/actions", response_model=Envelope[EvaluationDetail])
async def apply_evaluation_action(
    evaluationId: str,
    payload: EvaluationActionRequest,
    current_user=Depends(get_current_user),
    service: EvaluationService = Depends(get_evaluation_service),
):
    """对指定评测任务执行操作。"""
    response = await service.apply_action(evaluationId, payload, current_user)
    return success_payload(response.model_dump(by_alias=True))
