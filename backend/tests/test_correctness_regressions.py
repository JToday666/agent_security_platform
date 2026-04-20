from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, PropertyMock, patch

from sqlalchemy.exc import IntegrityError

from app.modules.auth.schemas import RegisterRequest
from app.modules.auth.service import AuthService
from app.modules.evaluations.schemas import EvaluationActionRequest
from app.modules.evaluations.service import EvaluationService
from app.modules.submissions.schemas import AgentSubmissionRequest
from app.modules.submissions.service import SubmissionService
from app.modules.user.schemas import ProfileUpdateRequest
from app.modules.user.service import UserService
from app.shared.config import settings
from app.shared.errors import ConflictError


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
        self.stored_refs: list[str] = []
        self.deleted_refs: list[str] = []
        self.payloads: list[dict[str, object]] = []

    def store(self, payload: dict[str, object]) -> str:
        self.payloads.append(payload)
        credential_ref = f"secret_{len(self.payloads)}"
        self.stored_refs.append(credential_ref)
        return credential_ref

    def load(self, credential_ref: str) -> dict[str, object]:
        return self.payloads[0]

    def delete(self, credential_ref: str) -> None:
        self.deleted_refs.append(credential_ref)


class FakeUploadFile:
    def __init__(self, content_type: str, content: bytes) -> None:
        self.content_type = content_type
        self._content = content

    async def read(self) -> bytes:
        return self._content


class EvaluationReadOnlyRepositoryStub:
    def __init__(self, run, datasets, report) -> None:
        self.run = run
        self.datasets = datasets
        self.report = report
        self.commit_calls = 0

    async def list_runs_for_user(self, user_id: int):
        return [self.run]

    async def get_run_by_public_id(self, public_id: str):
        return self.run

    async def load_run_datasets(self, run_id: int):
        return self.datasets

    async def load_run_report(self, run_id: int):
        return self.report

    async def load_related_for_runs(self, run_ids: list[int]):
        return {self.run.id: self.datasets}, {self.run.id: self.report} if self.report is not None else {}

    async def commit(self) -> None:
        self.commit_calls += 1

    async def refresh(self, entity) -> None:
        return None


class CorrectnessRegressionTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_register_maps_db_unique_conflict_to_business_conflict(self) -> None:
        repository = AuthRepositoryConflictStub()
        service = AuthService(repository)

        with self.assertRaises(ConflictError) as ctx:
            await service.register(
                RegisterRequest(
                    username="demo-user",
                    email="demo@example.com",
                    password="secret123",
                )
            )

        self.assertEqual(ctx.exception.code, 1002)
        self.assertEqual(ctx.exception.message, "用户名已被注册")
        self.assertEqual(repository.rollback_calls, 1)

    async def test_update_profile_maps_db_unique_conflict_to_business_conflict(self) -> None:
        repository = UserRepositoryConflictStub()
        service = UserService(repository)
        current_user = SimpleNamespace(id=1, username="alice", hashed_password="hash", avatar_url=None)

        with self.assertRaises(ConflictError) as ctx:
            await service.update_profile(ProfileUpdateRequest(username="bob"), current_user)

        self.assertEqual(ctx.exception.code, 1003)
        self.assertEqual(ctx.exception.message, "用户名已被占用")
        self.assertEqual(repository.rollback_calls, 1)

    async def test_submit_reuses_existing_run_after_request_id_conflict(self) -> None:
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

        self.assertEqual(response.evaluation_id, "eval_existing")
        self.assertEqual(response.status, "pending")
        self.assertEqual(credential_store.deleted_refs, ["secret_1"])
        self.assertEqual(repository.rollback_calls, 1)

    async def test_submit_cleans_up_credentials_when_run_creation_fails(self) -> None:
        repository = SubmissionRepositoryIdempotencyStub(
            create_error=RuntimeError("create run graph failed"),
            existing_run=None,
        )
        credential_store = MemoryCredentialStore()
        service = SubmissionService(repository, credential_store=credential_store)
        current_user = SimpleNamespace(id=1, username="demo-user")

        with self.assertRaises(RuntimeError):
            await service.submit(build_submission_payload(), current_user)

        self.assertEqual(credential_store.deleted_refs, ["secret_1"])
        self.assertEqual(repository.rollback_calls, 1)

    async def test_upload_avatar_deletes_written_file_when_persist_fails(self) -> None:
        repository = UploadingUserRepositoryStub(RuntimeError("db write failed"))
        service = UserService(repository)
        current_user = SimpleNamespace(id=1, username="alice", hashed_password="hash", avatar_url=None)
        avatar = FakeUploadFile(content_type="image/png", content=b"avatar-bytes")

        with tempfile.TemporaryDirectory() as tmpdir:
            avatars_root = Path(tmpdir)
            with patch.object(type(settings), "avatars_root", new_callable=PropertyMock, return_value=avatars_root):
                with self.assertRaises(RuntimeError):
                    await service.upload_avatar(avatar, current_user)

            self.assertEqual(list(avatars_root.iterdir()), [])
            self.assertEqual(repository.rollback_calls, 1)

    async def test_list_evaluations_does_not_finalize_expired_paused_runs(self) -> None:
        now = datetime.now(timezone.utc)
        run = SimpleNamespace(
            id=1,
            public_id="eval_1",
            agent_name="demo-agent",
            description=None,
            created_at=now,
            updated_at=now,
            status="paused",
            public_to_leaderboard=True,
            submit_method="api",
            finalization_reason=None,
            pause_used=True,
            pause_deadline_at=now - timedelta(minutes=5),
            execution_config={"parameters": {"difficulty": 0.5, "timeoutMinutes": 20, "retryEnabled": False}},
            total_samples=1,
            completed_samples=0,
        )
        datasets = [
            SimpleNamespace(
                dataset_code="A1_identity_leakage",
                dataset_name="Identity Leakage",
                status="paused",
            )
        ]
        repository = EvaluationReadOnlyRepositoryStub(run=run, datasets=datasets, report=None)
        service = EvaluationService(repository)
        current_user = SimpleNamespace(id=1, username="demo-user")

        with patch("app.modules.evaluations.service.lifecycle.finalize_run", new=AsyncMock()) as finalize_mock:
            response = await service.list_evaluations(current_user)

        self.assertEqual(response[0].status, "paused")
        self.assertEqual(repository.commit_calls, 0)
        finalize_mock.assert_not_awaited()

    async def test_get_evaluation_detail_does_not_finalize_expired_paused_runs(self) -> None:
        now = datetime.now(timezone.utc)
        run = SimpleNamespace(
            id=1,
            user_id=1,
            public_id="eval_1",
            agent_name="demo-agent",
            description=None,
            created_at=now,
            updated_at=now,
            status="paused",
            public_to_leaderboard=True,
            submit_method="api",
            finalization_reason=None,
            pause_used=True,
            pause_deadline_at=now - timedelta(minutes=5),
            execution_config={"parameters": {"difficulty": 0.5, "timeoutMinutes": 20, "retryEnabled": False}},
            total_samples=1,
            completed_samples=0,
        )
        datasets = [
            SimpleNamespace(
                dataset_code="A1_identity_leakage",
                dataset_name="Identity Leakage",
                status="paused",
            )
        ]
        repository = EvaluationReadOnlyRepositoryStub(run=run, datasets=datasets, report=None)
        service = EvaluationService(repository)
        current_user = SimpleNamespace(id=1, username="demo-user")

        with patch("app.modules.evaluations.service.lifecycle.finalize_run", new=AsyncMock()) as finalize_mock:
            response = await service.get_evaluation_detail("eval_1", current_user)

        self.assertEqual(response.status, "paused")
        self.assertEqual(repository.commit_calls, 0)
        finalize_mock.assert_not_awaited()

    async def test_apply_action_pause_delegates_to_lifecycle_module(self) -> None:
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
            execution_config={"parameters": {"difficulty": 0.5, "timeoutMinutes": 20, "retryEnabled": False}},
            total_samples=1,
            completed_samples=0,
        )
        repository = EvaluationReadOnlyRepositoryStub(run=run, datasets=[], report=None)
        repository.db = AsyncMock()
        service = EvaluationService(repository)
        current_user = SimpleNamespace(id=1, username="demo-user")
        lifecycle_module = SimpleNamespace(
            reconcile_run_timeout=AsyncMock(return_value=False),
            request_pause=unittest.mock.Mock(),
        )

        with patch.object(service.__class__, "_build_detail_snapshot", new=AsyncMock(return_value="snapshot")):
            with patch("app.modules.evaluations.service.lifecycle", new=lifecycle_module, create=True):
                response = await service.apply_action(
                    "eval_1",
                    EvaluationActionRequest(action="pause"),
                    current_user,
                )

        self.assertEqual(response, "snapshot")
        lifecycle_module.request_pause.assert_called_once()

    async def test_apply_action_cancel_delegates_to_lifecycle_module(self) -> None:
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
            execution_config={"parameters": {"difficulty": 0.5, "timeoutMinutes": 20, "retryEnabled": False}},
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

        with patch.object(service.__class__, "_build_detail_snapshot", new=AsyncMock(return_value="snapshot")):
            with patch("app.modules.evaluations.service.lifecycle", new=lifecycle_module, create=True):
                response = await service.apply_action(
                    "eval_1",
                    EvaluationActionRequest(action="cancel"),
                    current_user,
                )

        self.assertEqual(response, "snapshot")
        lifecycle_module.request_cancel.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
