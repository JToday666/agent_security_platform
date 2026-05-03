"""用户模块路由，负责资料与头像相关接口。"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.repository import UserRepository
from app.modules.user.schemas import AvatarUploadData, ProfileUpdateRequest, UserProfile
from app.modules.user.service import UserService
from app.modules.auth.dependencies import get_current_user
from app.platform.auth import get_db
from app.platform.http import success_payload
from app.platform.schemas import Envelope

router = APIRouter(prefix="/user", tags=["user"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """返回用户模块使用的服务实例。"""
    return UserService(UserRepository(db))


@router.get("/profile", response_model=Envelope[UserProfile])
async def get_profile(current_user=Depends(get_current_user), service: UserService = Depends(get_user_service)):
    """返回当前用户资料。"""
    response = await service.get_profile(current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.put("/profile", response_model=Envelope[UserProfile])
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user=Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """更新当前用户资料。"""
    response = await service.update_profile(payload, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.post("/avatar", response_model=Envelope[AvatarUploadData])
async def upload_avatar(
    avatar: UploadFile | None = File(default=None),
    current_user=Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """上传并保存当前用户头像。"""
    response = await service.upload_avatar(avatar, current_user)
    return success_payload(response.model_dump(by_alias=True))
