"""用户模块请求与响应模型。"""

from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.shared.schemas import CamelModel


class UserProfile(CamelModel):
    """用户资料响应体。"""

    id: int
    username: str
    email: EmailStr
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=CamelModel.model_config["alias_generator"])


class ProfileUpdateRequest(CamelModel):
    """更新用户资料的请求体。"""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    email: EmailStr | None = None

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("username cannot be empty")
        return value


class AvatarUploadData(CamelModel):
    """头像上传接口返回的数据。"""

    avatar_url: str
