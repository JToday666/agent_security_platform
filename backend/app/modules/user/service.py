"""用户模块服务，负责资料更新与头像上传。"""

import uuid
from pathlib import Path

from fastapi import UploadFile, status
from sqlalchemy.exc import IntegrityError

from app.modules.user.repository import UserRepository
from app.modules.user.schemas import AvatarUploadData, ProfileUpdateRequest, UserProfile
from app.shared.config import settings
from app.shared.errors import ConflictError, DomainError, ForbiddenError, ValidationDomainError
from app.shared.security import hash_password

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024


class UserService:
    """封装用户资料相关业务能力。"""

    def __init__(self, repository: UserRepository) -> None:
        """绑定用户资料服务使用的仓储实例。"""
        self.repository = repository

    async def get_profile(self, current_user) -> UserProfile:
        """返回当前用户资料。"""
        return UserProfile.model_validate(current_user)

    async def update_profile(self, payload: ProfileUpdateRequest, current_user) -> UserProfile:
        """更新当前用户可编辑的资料字段。"""
        if payload.email is not None:
            raise ForbiddenError("邮箱不可修改", code=1004)

        if payload.username is None and payload.password is None:
            raise ValidationDomainError("没有提供要修改的字段", http_status=status.HTTP_400_BAD_REQUEST, code=1000)

        if payload.username is not None and payload.username != current_user.username:
            if await self.repository.is_username_taken(payload.username, exclude_user_id=current_user.id):
                raise ConflictError("用户名已被占用", code=1003)
            current_user.username = payload.username

        if payload.password is not None:
            current_user.hashed_password = hash_password(payload.password)

        try:
            await self.repository.save_user(current_user)
            await self.repository.commit()
            await self.repository.refresh(current_user)
        except IntegrityError as exc:
            await self.repository.rollback()
            raise ConflictError("用户名已被占用", code=1003) from exc
        return UserProfile.model_validate(current_user)

    async def upload_avatar(self, avatar: UploadFile | None, current_user) -> AvatarUploadData:
        """保存用户头像并返回可访问地址。"""
        if avatar is None:
            raise ValidationDomainError("请选择要上传的头像", http_status=status.HTTP_400_BAD_REQUEST, code=1000)

        if avatar.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationDomainError("仅支持 JPG、PNG 格式", http_status=status.HTTP_400_BAD_REQUEST, code=1000)

        content = await avatar.read()
        if len(content) > MAX_AVATAR_SIZE:
            raise ValidationDomainError("头像大小不能超过 2MB", http_status=status.HTTP_400_BAD_REQUEST, code=1000)

        settings.avatars_root.mkdir(parents=True, exist_ok=True)
        extension = ALLOWED_IMAGE_TYPES[avatar.content_type]
        file_name = f"{current_user.id}_{uuid.uuid4().hex}{extension}"
        file_path = settings.avatars_root / file_name

        try:
            with Path(file_path).open("wb") as file_obj:
                file_obj.write(content)
        except Exception as exc:  # pragma: no cover - filesystem guard
            raise DomainError(
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                code=500,
                message="头像上传失败，请稍后重试",
            ) from exc

        current_user.avatar_url = f"/uploads/avatars/{file_name}"
        try:
            await self.repository.save_user(current_user)
            await self.repository.commit()
            await self.repository.refresh(current_user)
        except Exception:
            await self.repository.rollback()
            if file_path.exists():
                file_path.unlink()
            raise
        return AvatarUploadData(avatar_url=current_user.avatar_url)
