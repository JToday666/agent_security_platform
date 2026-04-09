from fastapi import status

from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import AuthSessionData, RegisterRequest, UserProfile
from app.shared.errors import AuthError, ConflictError, ValidationDomainError
from app.shared.security import create_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    async def login(self, username: str, password: str) -> AuthSessionData:
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
        username = payload.username.strip()
        email = payload.email.lower()

        if await self.repository.is_username_taken(username):
            raise ConflictError("用户名已被注册", code=1002)

        if await self.repository.is_email_taken(email):
            raise ConflictError("邮箱已被注册", code=1002)

        user = await self.repository.create_user(username, email, hash_password(payload.password))
        return AuthSessionData(
            token=create_access_token(user.id),
            user=UserProfile.model_validate(user),
        )

    async def me(self, current_user) -> UserProfile:
        return UserProfile.model_validate(current_user)
