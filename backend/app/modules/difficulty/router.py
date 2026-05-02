"""动态难度接口路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import get_current_user
from app.modules.difficulty.schemas import DifficultyPublishResult, DifficultyRecalculateRequest, DifficultyVersionResult
from app.modules.difficulty.service import DifficultyService
from app.shared.auth import get_db
from app.shared.http import success_payload
from app.shared.schemas import Envelope

router = APIRouter(prefix="/difficulty", tags=["difficulty"])


def get_difficulty_service(db: AsyncSession = Depends(get_db)) -> DifficultyService:
    return DifficultyService(db)


@router.post("/versions/recalculate", response_model=Envelope[DifficultyVersionResult])
async def recalculate_difficulty_version(
    payload: DifficultyRecalculateRequest,
    _current_user=Depends(get_current_user),
    service: DifficultyService = Depends(get_difficulty_service),
):
    response = await service.recalculate_version(
        base_version_code=payload.base_version_code,
        new_version_code=payload.new_version_code,
        stats_cutoff_at=payload.stats_cutoff_at,
    )
    return success_payload(response.model_dump(by_alias=True))


@router.post("/versions/{versionCode}/publish", response_model=Envelope[DifficultyPublishResult])
async def publish_difficulty_version(
    versionCode: str,
    _current_user=Depends(get_current_user),
    service: DifficultyService = Depends(get_difficulty_service),
):
    response = await service.publish_version(versionCode)
    return success_payload(response.model_dump(by_alias=True))
