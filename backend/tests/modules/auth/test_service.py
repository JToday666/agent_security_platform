from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.auth.schemas import RegisterRequest
from app.modules.auth.service import AuthService
from app.platform.errors import AuthError, ConflictError, ValidationDomainError


def make_integrity_error(detail: str) -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception(detail))


class AuthRepositoryConflictStub:
    def __init__(self) -> None:
        self.rollback_calls = 0

    async def is_username_taken(self, username: str) -> bool:
        return False

    async def is_email_taken(self, email: str) -> bool:
        return False

    async def create_user(self, username: str, email: str, hashed_password: str):
        raise make_integrity_error("users_username_key")

    async def rollback(self) -> None:
        self.rollback_calls += 1


class AuthRepositoryLoginStub:
    async def get_user_by_login_identifier(self, username: str):
        return None


@pytest.mark.asyncio
async def test_login_errors_carry_message_keys() -> None:
    service = AuthService(AuthRepositoryLoginStub())

    with pytest.raises(ValidationDomainError) as missing_credentials:
        await service.login(" ", "")
    assert missing_credentials.value.message_key == "errors.auth.missing_credentials"

    with pytest.raises(AuthError) as invalid_credentials:
        await service.login("demo-user", "wrong-password")
    assert invalid_credentials.value.message_key == "errors.auth.invalid_credentials"


@pytest.mark.asyncio
async def test_register_maps_db_unique_conflict_to_business_conflict() -> None:
    repository = AuthRepositoryConflictStub()
    service = AuthService(repository)

    try:
        await service.register(
            RegisterRequest(
                username="demo-user",
                email="demo@example.com",
                password="secret123",
            )
        )
    except ConflictError as exc:
        assert exc.code == 1002
        assert exc.message == "用户名已被注册"
        assert exc.message_key == "errors.auth.username_or_email_taken"
    else:
        raise AssertionError("expected ConflictError")

    assert repository.rollback_calls == 1
