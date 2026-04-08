from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_platform_user, get_db
from app.api.response import fail, success
from app.models.user import User
from app.schemas.agents import AgentSubmissionRequest
from app.services.submissions import SubmissionService

router = APIRouter(prefix="/agents", tags=["agents"])


def get_submission_service(db: AsyncSession = Depends(get_db)) -> SubmissionService:
    return SubmissionService(db)


@router.get("/submit-meta")
async def submit_meta(
    service: SubmissionService = Depends(get_submission_service),
):
    try:
        return success(data=await service.get_submit_meta())
    except HTTPException:
        raise
    except Exception:
        raise fail(status.HTTP_500_INTERNAL_SERVER_ERROR, 50000, "提交配置加载失败，请稍后重试。")


@router.post("/precheck")
async def precheck_submission(
    payload: AgentSubmissionRequest,
    current_user: User = Depends(get_current_platform_user),
    service: SubmissionService = Depends(get_submission_service),
):
    try:
        return success(data=await service.precheck(payload=payload, current_user=current_user))
    except HTTPException:
        raise
    except Exception:
        raise fail(status.HTTP_500_INTERNAL_SERVER_ERROR, 50000, "预检查失败，请稍后重试。")


@router.post("/submit")
async def submit_agent(
    payload: AgentSubmissionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_platform_user),
    service: SubmissionService = Depends(get_submission_service),
):
    try:
        return success(
            data=await service.submit(
                payload=payload,
                current_user=current_user,
                background_tasks=background_tasks,
            )
        )
    except HTTPException:
        raise
    except Exception:
        raise fail(status.HTTP_500_INTERNAL_SERVER_ERROR, 50000, "提交任务失败，请稍后重试。")
