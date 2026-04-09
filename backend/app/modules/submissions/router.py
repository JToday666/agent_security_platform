from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.submissions.repository import SubmissionRepository
from app.modules.submissions.schemas import (
    AgentSubmissionRequest,
    PrecheckResponse,
    SubmitMetaResponse,
    SubmitResponse,
)
from app.modules.submissions.service import SubmissionService
from app.shared.auth import get_current_user, get_db
from app.shared.http import success_payload
from app.shared.schemas import Envelope

router = APIRouter(prefix="/agents", tags=["agents"])


def get_submission_service(db: AsyncSession = Depends(get_db)) -> SubmissionService:
    return SubmissionService(SubmissionRepository(db))


@router.get("/submit-meta", response_model=Envelope[SubmitMetaResponse])
async def submit_meta(service: SubmissionService = Depends(get_submission_service)):
    response = await service.get_submit_meta()
    return success_payload(response.model_dump(by_alias=True))


@router.post("/precheck", response_model=Envelope[PrecheckResponse])
async def precheck_submission(
    payload: AgentSubmissionRequest,
    current_user=Depends(get_current_user),
    service: SubmissionService = Depends(get_submission_service),
):
    response = await service.precheck(payload, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.post("/submit", response_model=Envelope[SubmitResponse])
async def submit_agent(
    payload: AgentSubmissionRequest,
    current_user=Depends(get_current_user),
    service: SubmissionService = Depends(get_submission_service),
):
    response = await service.submit(payload, current_user)
    return success_payload(response.model_dump(by_alias=True))
