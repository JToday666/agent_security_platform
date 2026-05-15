from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.modules.difficulty.service import DifficultyService
from app.platform.errors import ConflictError, NotFoundError


class ScalarResult:
    def __init__(self, value) -> None:
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class DifficultyDbStub:
    def __init__(self, execute_values) -> None:
        self.execute_values = list(execute_values)

    async def execute(self, statement):
        return ScalarResult(self.execute_values.pop(0))


@pytest.mark.asyncio
async def test_recalculate_version_duplicate_carries_message_key() -> None:
    service = DifficultyService(DifficultyDbStub([SimpleNamespace(version_code="v1")]))

    with pytest.raises(ConflictError) as exc:
        await service.recalculate_version(
            base_version_code="legacy_current", new_version_code="v1"
        )

    assert exc.value.message_key == "errors.difficulty.duplicate_version"


@pytest.mark.asyncio
async def test_publish_version_missing_version_carries_message_key() -> None:
    service = DifficultyService(DifficultyDbStub([None]))

    with pytest.raises(NotFoundError) as exc:
        await service.publish_version("missing")

    assert exc.value.message_key == "errors.difficulty.not_found"
