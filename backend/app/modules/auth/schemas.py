"""认证模块请求与响应模型。"""

from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.shared.schemas import CamelModel


class LoginRequest(CamelModel):
    """登录接口请求体。"""

    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """清理登录标识前后空白，供登录接口入参复用。"""
        return value.strip()


class RegisterRequest(CamelModel):
    """注册接口请求体。"""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """规范注册用户名格式并拦截空白值。"""
        value = value.strip()
        if not value:
            raise ValueError("username cannot be empty")
        return value


class UserProfile(CamelModel):
    """认证接口返回的用户资料。"""

    id: int
    username: str
    email: EmailStr
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=CamelModel.model_config["alias_generator"])


class AuthSessionData(CamelModel):
    """登录或注册成功后的会话信息。"""

    token: str
    user: UserProfile
