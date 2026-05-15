from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import mock_open, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.user.schemas import ProfileUpdateRequest
from app.modules.user.service import MAX_AVATAR_SIZE, UserService
from app.platform.errors import ConflictError, ForbiddenError, ValidationDomainError


def make_integrity_error(detail: str) -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception(detail))


class UserRepositoryConflictStub:
    def __init__(self) -> None:
        self.rollback_calls = 0

    async def is_username_taken(
        self, username: str, exclude_user_id: int | None = None
    ) -> bool:
        return False

    async def save_user(self, user):
        raise make_integrity_error("users_username_key")

    async def rollback(self) -> None:
        self.rollback_calls += 1


class UserRepositoryTakenStub:
    async def is_username_taken(
        self, username: str, exclude_user_id: int | None = None
    ) -> bool:
        return True


class EmptyUserRepositoryStub:
    pass


class UploadingUserRepositoryStub:
    def __init__(self, error: Exception) -> None:
        self.error = error
        self.rollback_calls = 0

    async def save_user(self, user):
        raise self.error

    async def rollback(self) -> None:
        self.rollback_calls += 1


class FakeUploadFile:
    def __init__(self, content_type: str, content: bytes) -> None:
        self.content_type = content_type
        self._content = content

    async def read(self) -> bytes:
        return self._content


@pytest.mark.asyncio
async def test_update_profile_maps_db_unique_conflict_to_business_conflict() -> None:
    repository = UserRepositoryConflictStub()
    service = UserService(repository)
    current_user = SimpleNamespace(
        id=1, username="alice", hashed_password="hash", avatar_url=None
    )

    with pytest.raises(ConflictError) as ctx:
        await service.update_profile(ProfileUpdateRequest(username="bob"), current_user)

    assert ctx.value.code == 1003
    assert ctx.value.message == "用户名已被占用"
    assert ctx.value.message_key == "errors.user.username_taken"
    assert repository.rollback_calls == 1


@pytest.mark.asyncio
async def test_update_profile_validation_errors_carry_message_keys() -> None:
    service = UserService(EmptyUserRepositoryStub())
    current_user = SimpleNamespace(
        id=1, username="alice", hashed_password="hash", avatar_url=None
    )

    with pytest.raises(ForbiddenError) as immutable_email:
        await service.update_profile(
            ProfileUpdateRequest(email="alice@example.com"), current_user
        )
    assert immutable_email.value.message_key == "errors.user.email_immutable"

    with pytest.raises(ValidationDomainError) as empty_profile:
        await service.update_profile(ProfileUpdateRequest(), current_user)
    assert empty_profile.value.message_key == "errors.user.profile_empty"

    service = UserService(UserRepositoryTakenStub())
    with pytest.raises(ConflictError) as username_taken:
        await service.update_profile(ProfileUpdateRequest(username="bob"), current_user)
    assert username_taken.value.message_key == "errors.user.username_taken"


@pytest.mark.asyncio
async def test_upload_avatar_validation_errors_carry_message_keys() -> None:
    service = UserService(EmptyUserRepositoryStub())
    current_user = SimpleNamespace(
        id=1, username="alice", hashed_password="hash", avatar_url=None
    )

    with pytest.raises(ValidationDomainError) as missing_avatar:
        await service.upload_avatar(None, current_user)
    assert missing_avatar.value.message_key == "errors.user.avatar_missing"

    with pytest.raises(ValidationDomainError) as invalid_type:
        await service.upload_avatar(
            FakeUploadFile(content_type="image/gif", content=b"avatar"), current_user
        )
    assert invalid_type.value.message_key == "errors.user.avatar_type"

    with pytest.raises(ValidationDomainError) as oversized:
        await service.upload_avatar(
            FakeUploadFile(
                content_type="image/png", content=b"x" * (MAX_AVATAR_SIZE + 1)
            ),
            current_user,
        )
    assert oversized.value.message_key == "errors.user.avatar_size"


@pytest.mark.asyncio
async def test_upload_avatar_deletes_written_file_when_persist_fails() -> None:
    repository = UploadingUserRepositoryStub(RuntimeError("db write failed"))
    avatars_root = Path("runtime/test-avatars/mock")
    service = UserService(repository, avatars_root=avatars_root)
    current_user = SimpleNamespace(
        id=1, username="alice", hashed_password="hash", avatar_url=None
    )
    avatar = FakeUploadFile(content_type="image/png", content=b"avatar-bytes")

    with patch.object(Path, "mkdir") as mkdir_mock, patch.object(
        Path, "open", mock_open()
    ) as open_mock, patch.object(
        Path,
        "exists",
        return_value=True,
    ), patch.object(
        Path, "unlink"
    ) as unlink_mock:
        with pytest.raises(RuntimeError):
            await service.upload_avatar(avatar, current_user)

    mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
    open_mock.assert_called_once_with("wb")
    unlink_mock.assert_called_once()
    assert repository.rollback_calls == 1
