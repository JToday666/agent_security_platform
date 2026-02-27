from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip()


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("username cannot be empty")
        return value


class UserProfile(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar_url: str | None = Field(default=None, alias="avatarUrl")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LoginRegisterResponse(BaseModel):
    token: str
    user: UserProfile


class ProfileUpdateRequest(BaseModel):
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
