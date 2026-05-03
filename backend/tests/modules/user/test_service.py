from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.user.schemas import ProfileUpdateRequest
from app.modules.user.service import UserService
from app.platform.config import settings
from app.platform.errors import ConflictError


def make_integrity_error(detail: str) -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception(detail))


class UserRepositoryConflictStub:
    def __init__(self) -> None:
        self.rollback_calls = 0

    async def is_username_taken(self, username: str, exclude_user_id: int | None = None) -> bool:
        return False

    async def save_user(self, user):
        raise make_integrity_error("users_username_key")

    async def rollback(self) -> None:
        self.rollback_calls += 1


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
    current_user = SimpleNamespace(id=1, username="alice", hashed_password="hash", avatar_url=None)

    with pytest.raises(ConflictError) as ctx:
        await service.update_profile(ProfileUpdateRequest(username="bob"), current_user)

    assert ctx.value.code == 1003
    assert ctx.value.message == "用户名已被占用"
    assert repository.rollback_calls == 1


@pytest.mark.asyncio
async def test_upload_avatar_deletes_written_file_when_persist_fails() -> None:
    repository = UploadingUserRepositoryStub(RuntimeError("db write failed"))
    service = UserService(repository)
    current_user = SimpleNamespace(id=1, username="alice", hashed_password="hash", avatar_url=None)
    avatar = FakeUploadFile(content_type="image/png", content=b"avatar-bytes")

    with TemporaryDirectory() as tmpdir:
        avatars_root = Path(tmpdir)
        with patch.object(type(settings), "avatars_root", new_callable=PropertyMock, return_value=avatars_root):
            with pytest.raises(RuntimeError):
                await service.upload_avatar(avatar, current_user)

        assert list(avatars_root.iterdir()) == []
        assert repository.rollback_calls == 1
