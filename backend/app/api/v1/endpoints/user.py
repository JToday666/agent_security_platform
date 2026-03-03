import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.response import fail, success
from app.core.security import hash_password
from app.crud import is_username_taken, save_user
from app.models.user import User
from app.schemas.auth import ProfileUpdateRequest, UserProfile

router = APIRouter(prefix="/user", tags=["user"])

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024
AVATAR_DIR = Path("uploads") / "avatars"


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    user_data = UserProfile.model_validate(current_user).model_dump(by_alias=True)
    return success(data=user_data)


@router.put("/profile")
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.email is not None:
        raise fail(status.HTTP_403_FORBIDDEN, 1004, "邮箱不可修改")

    if payload.username is None and payload.password is None:
        raise fail(status.HTTP_400_BAD_REQUEST, 1000, "没有提供要修改的字段")

    if payload.username is not None and payload.username != current_user.username:
        if await is_username_taken(db, payload.username, exclude_user_id=current_user.id):
            raise fail(status.HTTP_409_CONFLICT, 1003, "用户名已被占用")
        current_user.username = payload.username

    if payload.password is not None:
        current_user.hashed_password = hash_password(payload.password)

    await save_user(db, current_user)

    user_data = UserProfile.model_validate(current_user).model_dump(by_alias=True)
    return success(data=user_data)


@router.post("/avatar")
async def upload_avatar(
    avatar: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if avatar is None:
        raise fail(status.HTTP_400_BAD_REQUEST, 1000, "请选择要上传的头像")

    if avatar.content_type not in ALLOWED_IMAGE_TYPES:
        raise fail(status.HTTP_400_BAD_REQUEST, 1000, "仅支持 JPG、PNG 格式")

    content = await avatar.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise fail(status.HTTP_400_BAD_REQUEST, 1000, "头像大小不能超过 2MB")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    extension = ALLOWED_IMAGE_TYPES[avatar.content_type]
    file_name = f"{current_user.id}_{uuid.uuid4().hex}{extension}"
    file_path = AVATAR_DIR / file_name

    try:
        with open(file_path, "wb") as file_obj:
            file_obj.write(content)
    except Exception:
        raise fail(status.HTTP_500_INTERNAL_SERVER_ERROR, 500, "头像上传失败，请稍后重试")

    current_user.avatar_url = f"/uploads/avatars/{file_name}"
    await save_user(db, current_user)

    return success(data={"avatarUrl": current_user.avatar_url})
