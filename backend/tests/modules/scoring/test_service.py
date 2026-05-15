from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.scoring.service import (
    ScoringService,
    calculate_and_store_evaluation_score,
)
from app.platform.errors import NotFoundError, ValidationDomainError


class ScalarResult:
    def __init__(self, value) -> None:
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class ScoringDbStub:
    def __init__(self, *, get_value=None, execute_values=None) -> None:
        self.get_value = get_value
        self.execute_values = list(execute_values or [])

    async def get(self, model, row_id: int):
        return self.get_value

    async def execute(self, statement):
        return ScalarResult(self.execute_values.pop(0))


@pytest.mark.asyncio
async def test_calculate_score_errors_carry_message_keys() -> None:
    with pytest.raises(ValidationDomainError) as not_ended:
        await calculate_and_store_evaluation_score(
            ScoringDbStub(get_value=SimpleNamespace(status="running")), 1
        )
    assert not_ended.value.message_key == "errors.scoring.not_ended"

    with patch(
        "app.modules.scoring.service.load_score_observations",
        new=AsyncMock(return_value=[]),
    ):
        with pytest.raises(ValidationDomainError) as no_samples:
            await calculate_and_store_evaluation_score(
                ScoringDbStub(get_value=SimpleNamespace(status="completed")), 1
            )
    assert no_samples.value.message_key == "errors.scoring.no_samples"


@pytest.mark.asyncio
async def test_get_score_missing_score_carries_message_key() -> None:
    run = SimpleNamespace(id=1, public_id="eval_1", user_id=1)
    service = ScoringService(ScoringDbStub(execute_values=[run, None]))

    with pytest.raises(NotFoundError) as exc:
        await service.get_score("eval_1", SimpleNamespace(id=1))

    assert exc.value.message_key == "errors.scoring.not_found"
