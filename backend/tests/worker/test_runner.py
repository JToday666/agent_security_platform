from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.worker import runner


pytestmark = pytest.mark.worker


class FakeSession:
    def __init__(self, run=None) -> None:
        self.run = run or SimpleNamespace(id=1, status="running")
        self.rollback_calls = 0

    async def get(self, model, run_id):
        return self.run

    async def rollback(self) -> None:
        self.rollback_calls += 1

    async def refresh(self, entity) -> None:
        return None


class FakeSessionFactory:
    def __init__(self, session: FakeSession | None = None) -> None:
        self.session = session or FakeSession()

    def __call__(self):
        return self

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


@pytest.mark.asyncio
async def test_process_run_safely_marks_non_terminal_runs_failed() -> None:
    session = FakeSession(run=SimpleNamespace(id=1, status="running"))

    with patch.object(runner, "AsyncSessionLocal", new=FakeSessionFactory(session)), patch.object(
        runner,
        "process_claimed_run",
        new=AsyncMock(side_effect=RuntimeError("runner exploded")),
    ), patch.object(runner, "mark_run_failed", new=AsyncMock()) as mark_failed_mock, patch.object(
        runner.LOGGER,
        "exception",
    ) as log_mock:
        await runner._process_run_safely(1, "worker-test")

    mark_failed_mock.assert_awaited_once()
    log_mock.assert_called_once()


@pytest.mark.asyncio
async def test_run_worker_loop_recovers_from_process_errors() -> None:
    claims = [SimpleNamespace(id=1), None]
    sleep_calls = {"count": 0}

    async def fake_claim_next_run(db, worker_id: str):
        return claims.pop(0)

    async def fake_process_claimed_run(run_id: int, worker_id: str) -> None:
        raise RuntimeError("runner exploded")

    async def fake_sleep(seconds: float) -> None:
        sleep_calls["count"] += 1
        if sleep_calls["count"] >= 2:
            raise asyncio.CancelledError()

    with patch.object(runner, "AsyncSessionLocal", new=FakeSessionFactory()), patch.object(
        runner,
        "reconcile_expired_paused_runs",
        new=AsyncMock(return_value=[]),
    ), patch.object(runner, "claim_next_run", new=AsyncMock(side_effect=fake_claim_next_run)) as claim_mock, patch.object(
        runner,
        "mark_run_failed",
        new=AsyncMock(return_value=None),
    ), patch.object(runner, "process_claimed_run", new=AsyncMock(side_effect=fake_process_claimed_run)) as process_mock, patch.object(
        runner.LOGGER,
        "exception",
    ), patch.object(runner.asyncio, "sleep", new=AsyncMock(side_effect=fake_sleep)):
        with pytest.raises(asyncio.CancelledError):
            await runner.run_worker_loop("worker-test")

    assert claim_mock.await_count >= 2
    assert process_mock.await_count == 1


@pytest.mark.asyncio
async def test_run_worker_loop_reconciles_paused_runs_before_claiming() -> None:
    events: list[str] = []

    async def fake_reconcile(db) -> None:
        events.append("reconcile")

    async def fake_claim_next_run(db, worker_id: str):
        events.append("claim")
        return None

    async def fake_sleep(seconds: float) -> None:
        events.append("sleep")
        raise asyncio.CancelledError()

    with patch.object(runner, "AsyncSessionLocal", new=FakeSessionFactory()), patch.object(
        runner,
        "reconcile_expired_paused_runs",
        new=fake_reconcile,
        create=True,
    ), patch.object(runner, "claim_next_run", new=AsyncMock(side_effect=fake_claim_next_run)), patch.object(
        runner.asyncio,
        "sleep",
        new=AsyncMock(side_effect=fake_sleep),
    ):
        with pytest.raises(asyncio.CancelledError):
            await runner.run_worker_loop("worker-test")

    assert events == ["reconcile", "claim", "sleep"]


@pytest.mark.asyncio
async def test_run_worker_loop_can_claim_multiple_active_runs() -> None:
    claims = [SimpleNamespace(id=1), SimpleNamespace(id=2), None]
    processed: list[int] = []

    async def fake_claim_next_run(db, worker_id: str):
        return claims.pop(0)

    async def fake_process_claimed_run(run_id: int, worker_id: str) -> None:
        processed.append(run_id)

    async def fake_sleep(seconds: float) -> None:
        raise asyncio.CancelledError()

    with patch.object(runner, "AsyncSessionLocal", new=FakeSessionFactory()), patch.object(
        runner,
        "reconcile_expired_paused_runs",
        new=AsyncMock(return_value=[]),
    ), patch.object(runner, "claim_next_run", new=AsyncMock(side_effect=fake_claim_next_run)) as claim_mock, patch.object(
        runner,
        "process_claimed_run",
        new=AsyncMock(side_effect=fake_process_claimed_run),
    ) as process_mock, patch.object(
        runner.asyncio,
        "sleep",
        new=AsyncMock(side_effect=fake_sleep),
    ), patch.object(runner.settings, "WORKER_MAX_ACTIVE_RUNS", 2):
        with pytest.raises(asyncio.CancelledError):
            await runner.run_worker_loop("worker-test")

    assert claim_mock.await_count == 3
    assert process_mock.await_count == 2
    assert processed == [1, 2]
