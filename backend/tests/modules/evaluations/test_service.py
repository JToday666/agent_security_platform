from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.modules.evaluations.application.mappers import to_zulu
from app.modules.evaluations.schemas import EvaluationActionRequest
from app.modules.evaluations.service import EvaluationService
from app.platform.errors import ConflictError
from app.platform.i18n import set_current_locale


class EvaluationReadOnlyRepositoryStub:
    def __init__(self, run, datasets, report) -> None:
        self.run = run
        self.datasets = datasets
        self.report = report
        self.dataset_name_translations: dict[str, str] = {}
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

    async def load_dataset_name_translations(
        self, locale: str, dataset_codes: list[str]
    ):
        _ = locale
        return {
            dataset_code: self.dataset_name_translations[dataset_code]
            for dataset_code in dataset_codes
            if dataset_code in self.dataset_name_translations
        }

    async def commit(self) -> None:
        self.commit_calls += 1

    async def refresh(self, entity) -> None:
        return None

    async def rollback(self) -> None:
        self.rollback_calls += 1


def make_paused_run(now: datetime) -> SimpleNamespace:
    started_at = now - timedelta(minutes=10)
    finished_at = now - timedelta(minutes=2)
    return SimpleNamespace(
        id=1,
        user_id=1,
        public_id="eval_1",
        agent_name="demo-agent",
        description=None,
        created_at=now,
        updated_at=now,
        started_at=started_at,
        finished_at=finished_at,
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
        total_samples=12,
        completed_samples=7,
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
    assert response[0].finished_at == to_zulu(now - timedelta(minutes=2))
    assert repository.commit_calls == 0
    finalize_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_evaluations_localizes_dataset_names_at_response_time() -> None:
    now = datetime.now(timezone.utc)
    run = make_paused_run(now)
    datasets = [
        SimpleNamespace(
            dataset_code="A1_identity_leakage",
            dataset_name="身份泄露",
            status="paused",
        )
    ]
    repository = EvaluationReadOnlyRepositoryStub(
        run=run, datasets=datasets, report=None
    )
    repository.dataset_name_translations = {
        "A1_identity_leakage": "Identity Leakage"
    }
    service = EvaluationService(repository)
    current_user = SimpleNamespace(id=1, username="demo-user")
    token = set_current_locale("en-US")
    try:
        response = await service.list_evaluations(current_user)
    finally:
        token.reset()

    assert response[0].dataset_names == ["Identity Leakage"]


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
async def test_get_evaluation_detail_localizes_running_dataset_name() -> None:
    now = datetime.now(timezone.utc)
    run = make_paused_run(now)
    run.status = "running"
    run.pause_used = False
    run.pause_deadline_at = None
    datasets = [
        SimpleNamespace(
            dataset_code="A1_identity_leakage",
            dataset_name="身份泄露",
            status="running",
        )
    ]
    repository = EvaluationReadOnlyRepositoryStub(
        run=run, datasets=datasets, report=None
    )
    repository.dataset_name_translations = {
        "A1_identity_leakage": "Identity Leakage"
    }
    service = EvaluationService(repository)
    current_user = SimpleNamespace(id=1, username="demo-user")
    token = set_current_locale("en-US")
    try:
        response = await service.get_evaluation_detail("eval_1", current_user)
    finally:
        token.reset()

    assert response.dataset_names == ["Identity Leakage"]
    assert response.progress.running_dataset_name == "Identity Leakage"
    assert "Identity Leakage" in response.progress.status_text
    assert response.started_at == to_zulu(now - timedelta(minutes=10))
    assert response.finished_at == to_zulu(now - timedelta(minutes=2))
    assert response.progress.total_sample_count == 12
    assert response.progress.completed_sample_count == 7


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
        with (
            patch(
                "app.modules.evaluations.service.lifecycle",
                new=lifecycle_module,
                create=True,
            ),
            patch(
                "app.modules.evaluations.service.record_audit_log",
                new=AsyncMock(),
                create=True,
            ) as audit_mock,
        ):
            response = await service.apply_action(
                "eval_1", EvaluationActionRequest(action="pause"), current_user
            )

    assert response == "snapshot"
    lifecycle_module.request_pause.assert_called_once()
    audit_mock.assert_awaited_once()
    assert audit_mock.await_args.kwargs["action"] == "evaluation.paused"


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
        with (
            patch(
                "app.modules.evaluations.service.lifecycle",
                new=lifecycle_module,
                create=True,
            ),
            patch(
                "app.modules.evaluations.service.record_audit_log",
                new=AsyncMock(),
                create=True,
            ) as audit_mock,
        ):
            response = await service.apply_action(
                "eval_1", EvaluationActionRequest(action="cancel"), current_user
            )

    assert response == "snapshot"
    lifecycle_module.request_cancel.assert_awaited_once()
    audit_mock.assert_awaited_once()
    assert audit_mock.await_args.kwargs["action"] == "evaluation.cancelled"
    assert audit_mock.await_args.kwargs["actor_id"] == "1"
    assert audit_mock.await_args.kwargs["resource_id"] == "eval_1"


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
