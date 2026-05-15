from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.modules.evaluations.schemas import EvaluationActionRequest
from app.modules.evaluations.service import EvaluationService
from app.platform.errors import ConflictError


class EvaluationReadOnlyRepositoryStub:
    def __init__(self, run, datasets, report) -> None:
        self.run = run
        self.datasets = datasets
        self.report = report
        self.commit_calls = 0
        self.rollback_calls = 0

    async def list_runs_for_user(self, user_id: int):
        return [self.run]

    async def get_run_by_public_id(self, public_id: str):
        return self.run

    async def load_run_datasets(self, run_id: int):
        return self.datasets

    async def load_run_report(self, run_id: int):
        return self.report

    async def load_related_for_runs(self, run_ids: list[int]):
        return {self.run.id: self.datasets}, (
            {self.run.id: self.report} if self.report is not None else {}
        )

    async def commit(self) -> None:
        self.commit_calls += 1

    async def refresh(self, entity) -> None:
        return None

    async def rollback(self) -> None:
        self.rollback_calls += 1


def make_paused_run(now: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        user_id=1,
        public_id="eval_1",
        agent_name="demo-agent",
        description=None,
        created_at=now,
        updated_at=now,
        status="paused",
        public_to_leaderboard=True,
        leaderboard_display_mode="public",
        submit_method="api",
        finalization_reason=None,
        pause_used=True,
        pause_deadline_at=now - timedelta(minutes=5),
        execution_config={
            "parameters": {
                "difficulty": 0.5,
                "timeoutMinutes": 20,
                "retryEnabled": False,
            }
        },
        total_samples=1,
        completed_samples=0,
    )


@pytest.mark.asyncio
async def test_list_evaluations_does_not_finalize_expired_paused_runs() -> None:
    now = datetime.now(timezone.utc)
    run = make_paused_run(now)
    datasets = [
        SimpleNamespace(
            dataset_code="A1_identity_leakage",
            dataset_name="Identity Leakage",
            status="paused",
        )
    ]
    repository = EvaluationReadOnlyRepositoryStub(
        run=run, datasets=datasets, report=None
    )
    service = EvaluationService(repository)
    current_user = SimpleNamespace(id=1, username="demo-user")

    with patch(
        "app.modules.evaluations.service.lifecycle.finalize_run", new=AsyncMock()
    ) as finalize_mock:
        response = await service.list_evaluations(current_user)

    assert response[0].status == "paused"
    assert repository.commit_calls == 0
    finalize_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_evaluation_detail_does_not_finalize_expired_paused_runs() -> None:
    now = datetime.now(timezone.utc)
    run = make_paused_run(now)
    datasets = [
        SimpleNamespace(
            dataset_code="A1_identity_leakage",
            dataset_name="Identity Leakage",
            status="paused",
        )
    ]
    repository = EvaluationReadOnlyRepositoryStub(
        run=run, datasets=datasets, report=None
    )
    service = EvaluationService(repository)
    current_user = SimpleNamespace(id=1, username="demo-user")

    with patch(
        "app.modules.evaluations.service.lifecycle.finalize_run", new=AsyncMock()
    ) as finalize_mock:
        response = await service.get_evaluation_detail("eval_1", current_user)

    assert response.status == "paused"
    assert repository.commit_calls == 0
    finalize_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_action_pause_delegates_to_lifecycle_module() -> None:
    now = datetime.now(timezone.utc)
    run = SimpleNamespace(
        id=1,
        user_id=1,
        public_id="eval_1",
        agent_name="demo-agent",
        description=None,
        created_at=now,
        updated_at=now,
        status="running",
        public_to_leaderboard=True,
        submit_method="api",
        finalization_reason=None,
        pause_used=False,
        pause_deadline_at=None,
        execution_config={
            "parameters": {
                "difficulty": 0.5,
                "timeoutMinutes": 20,
                "retryEnabled": False,
            }
        },
        total_samples=1,
        completed_samples=0,
    )
    repository = EvaluationReadOnlyRepositoryStub(run=run, datasets=[], report=None)
    repository.db = AsyncMock()
    service = EvaluationService(repository)
    current_user = SimpleNamespace(id=1, username="demo-user")
    lifecycle_module = SimpleNamespace(
        reconcile_run_timeout=AsyncMock(return_value=False),
        request_pause=Mock(),
    )

    with patch.object(
        service.__class__,
        "_build_detail_snapshot",
        new=AsyncMock(return_value="snapshot"),
    ):
        with patch(
            "app.modules.evaluations.service.lifecycle",
            new=lifecycle_module,
            create=True,
        ):
            response = await service.apply_action(
                "eval_1", EvaluationActionRequest(action="pause"), current_user
            )

    assert response == "snapshot"
    lifecycle_module.request_pause.assert_called_once()


@pytest.mark.asyncio
async def test_apply_action_cancel_delegates_to_lifecycle_module() -> None:
    now = datetime.now(timezone.utc)
    run = SimpleNamespace(
        id=1,
        user_id=1,
        public_id="eval_1",
        agent_name="demo-agent",
        description=None,
        created_at=now,
        updated_at=now,
        status="running",
        public_to_leaderboard=True,
        submit_method="api",
        finalization_reason=None,
        pause_used=False,
        pause_deadline_at=None,
        execution_config={
            "parameters": {
                "difficulty": 0.5,
                "timeoutMinutes": 20,
                "retryEnabled": False,
            }
        },
        total_samples=1,
        completed_samples=0,
    )
    repository = EvaluationReadOnlyRepositoryStub(run=run, datasets=[], report=None)
    repository.db = AsyncMock()
    service = EvaluationService(repository)
    current_user = SimpleNamespace(id=1, username="demo-user")
    lifecycle_module = SimpleNamespace(
        reconcile_run_timeout=AsyncMock(return_value=False),
        request_cancel=AsyncMock(return_value=None),
    )

    with patch.object(
        service.__class__,
        "_build_detail_snapshot",
        new=AsyncMock(return_value="snapshot"),
    ):
        with patch(
            "app.modules.evaluations.service.lifecycle",
            new=lifecycle_module,
            create=True,
        ):
            response = await service.apply_action(
                "eval_1", EvaluationActionRequest(action="cancel"), current_user
            )

    assert response == "snapshot"
    lifecycle_module.request_cancel.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_action_pause_used_conflict_carries_message_key() -> None:
    now = datetime.now(timezone.utc)
    run = SimpleNamespace(
        id=1,
        user_id=1,
        public_id="eval_1",
        status="running",
        pause_used=True,
    )
    repository = EvaluationReadOnlyRepositoryStub(run=run, datasets=[], report=None)
    repository.db = AsyncMock()
    service = EvaluationService(repository)
    lifecycle_module = SimpleNamespace(
        reconcile_run_timeout=AsyncMock(return_value=False)
    )

    with patch(
        "app.modules.evaluations.service.lifecycle", new=lifecycle_module, create=True
    ):
        with pytest.raises(ConflictError) as exc:
            await service.apply_action(
                "eval_1",
                EvaluationActionRequest(action="pause"),
                SimpleNamespace(id=1, username="demo-user"),
            )

    assert exc.value.message_key == "errors.evaluations.pause_used"
    assert repository.rollback_calls == 1


@pytest.mark.asyncio
async def test_apply_action_state_conflict_carries_message_key_and_params() -> None:
    now = datetime.now(timezone.utc)
    run = SimpleNamespace(
        id=1,
        user_id=1,
        public_id="eval_1",
        status="completed",
        pause_used=False,
    )
    repository = EvaluationReadOnlyRepositoryStub(run=run, datasets=[], report=None)
    repository.db = AsyncMock()
    service = EvaluationService(repository)
    lifecycle_module = SimpleNamespace(
        reconcile_run_timeout=AsyncMock(return_value=False)
    )

    with patch(
        "app.modules.evaluations.service.lifecycle", new=lifecycle_module, create=True
    ):
        with pytest.raises(ConflictError) as exc:
            await service.apply_action(
                "eval_1",
                EvaluationActionRequest(action="pause"),
                SimpleNamespace(id=1, username="demo-user"),
            )

    assert exc.value.message_key == "errors.evaluations.state_action_not_allowed"
    assert exc.value.message_params == {"action": "pause"}
    assert repository.rollback_calls == 1
