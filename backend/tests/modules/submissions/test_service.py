from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.submissions.schemas import AgentSubmissionRequest
from app.modules.submissions.service import SubmissionService


def make_integrity_error(detail: str) -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception(detail))


def build_submission_payload() -> AgentSubmissionRequest:
    return AgentSubmissionRequest.model_validate(
        {
            "agentName": "demo-agent",
            "description": "nightly run",
            "submitMethod": "api",
            "api": {
                "baseUrl": "https://example.com/agent",
                "token": "sk-demo",
            },
            "parameters": {
                "difficulty": 0.5,
                "timeoutMinutes": 20,
                "retryEnabled": False,
            },
            "publicToLeaderboard": True,
            "datasetIds": ["A1_identity_leakage"],
            "requestId": "submit_20260409_demo001",
        }
    )


class SubmissionRepositoryIdempotencyStub:
    def __init__(self, create_error: Exception, existing_run) -> None:
        self.create_error = create_error
        self.existing_run = existing_run
        self.lookup_calls = 0
        self.rollback_calls = 0

    async def get_existing_run(self, user_id: int, request_id: str):
        self.lookup_calls += 1
        if self.lookup_calls == 1:
            return None
        return self.existing_run

    async def resolve_dataset_selection(self, ordered_dataset_ids: list[str], difficulty: float):
        return {
            "dataset_names": {"A1_identity_leakage": "Identity Leakage"},
            "sample_rows": [SimpleNamespace(id=101)],
            "matched_counts": {"A1_identity_leakage": 1},
        }

    async def create_run_graph(self, **kwargs):
        raise self.create_error

    async def rollback(self) -> None:
        self.rollback_calls += 1


class MemoryCredentialStore:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []
        self.deleted_refs: list[str] = []

    def store(self, payload: dict[str, object]) -> str:
        self.payloads.append(payload)
        return f"secret_{len(self.payloads)}"

    def load(self, credential_ref: str) -> dict[str, object]:
        return self.payloads[0]

    def delete(self, credential_ref: str) -> None:
        self.deleted_refs.append(credential_ref)


@pytest.mark.asyncio
async def test_submit_reuses_existing_run_after_request_id_conflict() -> None:
    existing_run = SimpleNamespace(
        public_id="eval_existing",
        status="pending",
        created_at=datetime(2026, 4, 9, 12, 0, tzinfo=timezone.utc),
    )
    repository = SubmissionRepositoryIdempotencyStub(
        create_error=make_integrity_error("uq_test_runs_user_id_request_id"),
        existing_run=existing_run,
    )
    credential_store = MemoryCredentialStore()
    service = SubmissionService(repository, credential_store=credential_store)
    current_user = SimpleNamespace(id=1, username="demo-user")

    response = await service.submit(build_submission_payload(), current_user)

    assert response.evaluation_id == "eval_existing"
    assert response.status == "pending"
    assert credential_store.deleted_refs == ["secret_1"]
    assert repository.rollback_calls == 1


@pytest.mark.asyncio
async def test_submit_cleans_up_credentials_when_run_creation_fails() -> None:
    repository = SubmissionRepositoryIdempotencyStub(
        create_error=RuntimeError("create run graph failed"),
        existing_run=None,
    )
    credential_store = MemoryCredentialStore()
    service = SubmissionService(repository, credential_store=credential_store)
    current_user = SimpleNamespace(id=1, username="demo-user")

    with pytest.raises(RuntimeError):
        await service.submit(build_submission_payload(), current_user)

    assert credential_store.deleted_refs == ["secret_1"]
    assert repository.rollback_calls == 1
