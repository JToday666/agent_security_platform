from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.modules.auth.schemas import RegisterRequest
from app.modules.auth.service import AuthService
from app.shared.errors import ConflictError


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
    else:
        raise AssertionError("expected ConflictError")

    assert repository.rollback_calls == 1
