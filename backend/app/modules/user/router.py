from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.repository import UserRepository
from app.modules.user.schemas import AvatarUploadData, ProfileUpdateRequest, UserProfile
from app.modules.user.service import UserService
from app.shared.auth import get_current_user, get_db
from app.shared.http import success_payload
from app.shared.schemas import Envelope

router = APIRouter(prefix="/user", tags=["user"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("/profile", response_model=Envelope[UserProfile])
async def get_profile(current_user=Depends(get_current_user), service: UserService = Depends(get_user_service)):
    response = await service.get_profile(current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.put("/profile", response_model=Envelope[UserProfile])
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user=Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    response = await service.update_profile(payload, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.post("/avatar", response_model=Envelope[AvatarUploadData])
async def upload_avatar(
    avatar: UploadFile | None = File(default=None),
    current_user=Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    response = await service.upload_avatar(avatar, current_user)
    return success_payload(response.model_dump(by_alias=True))
