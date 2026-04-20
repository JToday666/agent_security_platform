"""认证模块服务，负责登录注册等业务编排。"""

from fastapi import status
from sqlalchemy.exc import IntegrityError

from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import AuthSessionData, RegisterRequest, UserProfile
from app.shared.errors import AuthError, ConflictError, ValidationDomainError
from app.shared.security import create_access_token, hash_password, verify_password


def integrity_error_text(exc: IntegrityError) -> str:
    """提取数据库完整性异常中的关键信息。"""
    return f"{exc} {getattr(exc, 'orig', '')}".lower()


class AuthService:
    """封装认证相关业务能力。"""

    def __init__(self, repository: AuthRepository) -> None:
        """绑定认证流程使用的仓储实例。"""
        self.repository = repository

    async def login(self, username: str, password: str) -> AuthSessionData:
        """校验用户凭据并返回登录结果。"""
        normalized_username = username.strip()
        if not normalized_username or not password:
            raise ValidationDomainError("用户名和密码不能为空", http_status=status.HTTP_400_BAD_REQUEST, code=1000)

        user = await self.repository.get_user_by_login_identifier(normalized_username)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthError("用户名或密码错误", code=1001)

        return AuthSessionData(
            token=create_access_token(user.id),
            user=UserProfile.model_validate(user),
        )

    async def register(self, payload: RegisterRequest) -> AuthSessionData:
        """创建新用户并返回注册结果。"""
        username = payload.username.strip()
        email = payload.email.lower()

        if await self.repository.is_username_taken(username):
            raise ConflictError("用户名已被注册", code=1002)

        if await self.repository.is_email_taken(email):
            raise ConflictError("邮箱已被注册", code=1002)

        try:
            user = await self.repository.create_user(username, email, hash_password(payload.password))
            await self.repository.commit()
            await self.repository.refresh(user)
        except IntegrityError as exc:
            await self.repository.rollback()
            detail = integrity_error_text(exc)
            if "email" in detail:
                raise ConflictError("邮箱已被注册", code=1002) from exc
            raise ConflictError("用户名已被注册", code=1002) from exc
        return AuthSessionData(
            token=create_access_token(user.id),
            user=UserProfile.model_validate(user),
        )

    async def me(self, current_user) -> UserProfile:
        """返回当前用户的资料快照。"""
        return UserProfile.model_validate(current_user)
