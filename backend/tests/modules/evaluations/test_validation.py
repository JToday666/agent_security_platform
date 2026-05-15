from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.modules.evaluations.application.validation import validate_submission_payload
from app.modules.evaluations.schemas import EvaluationCreateRequest
from app.platform.errors import ValidationDomainError
from app.platform.i18n import set_current_locale


def build_payload(**overrides) -> EvaluationCreateRequest:
    payload = {
        "requestId": "req_123456",
        "submitMethod": "api",
        "agentId": "agt_demo",
        "datasetIds": ["A1_identity_leakage"],
        "parameters": {"difficulty": 0.5, "timeoutMinutes": 15, "maxSteps": 30},
        "publicToLeaderboard": True,
        "leaderboardDisplayMode": "public",
    }
    payload.update(overrides)
    return EvaluationCreateRequest.model_validate(payload)


class EvaluationValidationRepositoryStub:
    async def get_agent_by_public_id(self, agent_id: str):
        return SimpleNamespace(id=1, public_id=agent_id, user_id=1, status="active")

    async def resolve_dataset_selection(
        self, dataset_ids: list[str], difficulty: float
    ):
        return {
            "dataset_names": ["身份泄露"],
            "sample_rows": [SimpleNamespace(id=1)],
            "matched_counts": {"A1_identity_leakage": 1},
        }


@pytest.mark.asyncio
async def test_validate_submission_payload_localizes_public_leaderboard_warning() -> (
    None
):
    token = set_current_locale("en-US")
    try:
        warnings, selection, agent = await validate_submission_payload(
            EvaluationValidationRepositoryStub(),
            build_payload(),
            SimpleNamespace(id=1),
        )
    finally:
        token.reset()

    assert warnings == [
        {
            "code": "PUBLIC_LEADERBOARD",
            "message": "This result will appear on the public leaderboard. Make sure the description contains no sensitive information.",
        }
    ]
    assert selection["dataset_ids"] == ["A1_identity_leakage"]
    assert agent.public_id == "agt_demo"


@pytest.mark.asyncio
async def test_validate_submission_payload_sets_message_key_for_dataset_required() -> (
    None
):
    with pytest.raises(ValidationDomainError) as exc:
        await validate_submission_payload(
            EvaluationValidationRepositoryStub(),
            build_payload(datasetIds=[]),
            SimpleNamespace(id=1),
        )

    assert exc.value.message_key == "errors.evaluations.dataset_required"
