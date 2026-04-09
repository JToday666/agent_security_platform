from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.shared.schemas import CamelModel


class LoginRequest(CamelModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip()


class RegisterRequest(CamelModel):
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


class UserProfile(CamelModel):
    id: int
    username: str
    email: EmailStr
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=CamelModel.model_config["alias_generator"])


class AuthSessionData(CamelModel):
    token: str
    user: UserProfile
