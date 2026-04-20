"""认证模块路由，负责注册登录与当前用户信息接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import AuthSessionData, LoginRequest, RegisterRequest, UserProfile
from app.modules.auth.service import AuthService
from app.modules.auth.dependencies import get_current_user
from app.shared.auth import get_db
from app.shared.http import success_payload
from app.shared.schemas import Envelope

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """返回认证模块使用的服务实例。"""
    return AuthService(AuthRepository(db))


@router.post("/login", response_model=Envelope[AuthSessionData])
async def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)):
    """处理用户登录请求。"""
    response = await service.login(payload.username, payload.password)
    return success_payload(response.model_dump(by_alias=True))


@router.post("/register", response_model=Envelope[AuthSessionData])
async def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    """处理用户注册请求。"""
    response = await service.register(payload)
    return success_payload(response.model_dump(by_alias=True))


@router.get("/me", response_model=Envelope[UserProfile])
async def me(current_user=Depends(get_current_user), service: AuthService = Depends(get_auth_service)):
    """返回当前登录用户信息。"""
    response = await service.me(current_user)
    return success_payload(response.model_dump(by_alias=True))
