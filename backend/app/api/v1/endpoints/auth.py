from fastapi import APIRouter, Depends, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.response import fail, success
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserProfile

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    username = payload.username.strip()
    if not username or not payload.password:
        raise fail(status.HTTP_400_BAD_REQUEST, 1000, "用户名和密码不能为空")

    result = await db.execute(
        select(User).where(or_(User.username == username, User.email == username.lower()))
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise fail(status.HTTP_401_UNAUTHORIZED, 1001, "用户名或密码错误")

    token = create_access_token(user.id)
    user_data = UserProfile.model_validate(user).model_dump(by_alias=True)
    return success(data={"token": token, "user": user_data})


@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    username = payload.username.strip()
    email = payload.email.lower()

    exists_username = await db.execute(select(User).where(User.username == username))
    if exists_username.scalar_one_or_none() is not None:
        raise fail(status.HTTP_409_CONFLICT, 1002, "用户名已被注册")

    exists_email = await db.execute(select(User).where(User.email == email))
    if exists_email.scalar_one_or_none() is not None:
        raise fail(status.HTTP_409_CONFLICT, 1002, "邮箱已被注册")

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    user_data = UserProfile.model_validate(user).model_dump(by_alias=True)
    return success(data={"token": token, "user": user_data})


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    user_data = UserProfile.model_validate(current_user).model_dump(by_alias=True)
    return success(data=user_data)
