"""排行榜接口路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.dependencies import get_current_user
from app.modules.leaderboards.schemas import (
    LeaderboardSnapshotCreateRequest,
    LeaderboardSnapshotResponse,
)
from app.modules.leaderboards.service import LeaderboardService
from app.platform.auth import get_db
from app.platform.http import success_payload
from app.platform.schemas import Envelope

router = APIRouter(prefix="/leaderboards", tags=["leaderboards"])


def get_leaderboard_service(db: AsyncSession = Depends(get_db)) -> LeaderboardService:
    return LeaderboardService(db)


@router.post("/snapshots", response_model=Envelope[LeaderboardSnapshotResponse])
async def create_leaderboard_snapshot(
    payload: LeaderboardSnapshotCreateRequest | None = None,
    current_user=Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    request = payload or LeaderboardSnapshotCreateRequest()
    response = await service.create_snapshot(
        score_model_version=request.score_model_version,
        benchmark_version=request.benchmark_version,
        current_user=current_user,
    )
    return success_payload(response.model_dump(by_alias=True))


@router.get("/current", response_model=Envelope[LeaderboardSnapshotResponse])
async def get_current_leaderboard(
    service: LeaderboardService = Depends(get_leaderboard_service),
):
    response = await service.get_current_snapshot()
    return success_payload(response.model_dump(by_alias=True))
