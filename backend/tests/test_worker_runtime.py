from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.worker.main import build_worker_id
from app.worker import runner


class FakeSession:
    async def get(self, model, run_id):
        return SimpleNamespace(id=run_id, status="running")

    async def rollback(self) -> None:
        return None

    async def refresh(self, entity) -> None:
        return None


class FakeSessionFactory:
    def __call__(self):
        return self

    async def __aenter__(self):
        return FakeSession()

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class WorkerRuntimeTestCase(unittest.IsolatedAsyncioTestCase):
    def test_build_worker_id_is_unique_per_call(self) -> None:
        first = build_worker_id()
        second = build_worker_id()

        self.assertTrue(first.startswith("worker-"))
        self.assertTrue(second.startswith("worker-"))
        self.assertNotEqual(first, second)

    async def test_run_worker_loop_recovers_from_process_errors(self) -> None:
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

        with patch.object(runner, "AsyncSessionLocal", new=FakeSessionFactory()), \
             patch.object(runner, "reconcile_expired_paused_runs", new=AsyncMock(return_value=[])), \
             patch.object(runner, "claim_next_run", new=AsyncMock(side_effect=fake_claim_next_run)) as claim_mock, \
             patch.object(runner, "mark_run_failed", new=AsyncMock(return_value=None)), \
             patch.object(runner, "process_claimed_run", new=AsyncMock(side_effect=fake_process_claimed_run)) as process_mock, \
             patch.object(runner.LOGGER, "exception"), \
             patch.object(runner.asyncio, "sleep", new=AsyncMock(side_effect=fake_sleep)):
            with self.assertRaises(asyncio.CancelledError):
                await runner.run_worker_loop("worker-test")

        self.assertGreaterEqual(claim_mock.await_count, 2)
        self.assertEqual(process_mock.await_count, 1)

    async def test_run_worker_loop_reconciles_paused_runs_before_claiming(self) -> None:
        events: list[str] = []

        async def fake_reconcile(db) -> None:
            events.append("reconcile")

        async def fake_claim_next_run(db, worker_id: str):
            events.append("claim")
            return None

        async def fake_sleep(seconds: float) -> None:
            events.append("sleep")
            raise asyncio.CancelledError()

        with patch.object(runner, "AsyncSessionLocal", new=FakeSessionFactory()), \
             patch.object(runner, "reconcile_expired_paused_runs", new=fake_reconcile, create=True), \
             patch.object(runner, "claim_next_run", new=AsyncMock(side_effect=fake_claim_next_run)), \
             patch.object(runner.asyncio, "sleep", new=AsyncMock(side_effect=fake_sleep)):
            with self.assertRaises(asyncio.CancelledError):
                await runner.run_worker_loop("worker-test")

        self.assertEqual(events, ["reconcile", "claim", "sleep"])

    async def test_run_worker_loop_can_claim_multiple_active_runs(self) -> None:
        claims = [SimpleNamespace(id=1), SimpleNamespace(id=2), None]
        processed: list[int] = []

        async def fake_claim_next_run(db, worker_id: str):
            return claims.pop(0)

        async def fake_process_claimed_run(run_id: int, worker_id: str) -> None:
            processed.append(run_id)

        async def fake_sleep(seconds: float) -> None:
            raise asyncio.CancelledError()

        with patch.object(runner, "AsyncSessionLocal", new=FakeSessionFactory()), \
             patch.object(runner, "reconcile_expired_paused_runs", new=AsyncMock(return_value=[])), \
             patch.object(runner, "claim_next_run", new=AsyncMock(side_effect=fake_claim_next_run)) as claim_mock, \
             patch.object(runner, "process_claimed_run", new=AsyncMock(side_effect=fake_process_claimed_run)) as process_mock, \
             patch.object(runner.asyncio, "sleep", new=AsyncMock(side_effect=fake_sleep)), \
             patch.object(runner.settings, "WORKER_MAX_ACTIVE_RUNS", 2):
            with self.assertRaises(asyncio.CancelledError):
                await runner.run_worker_loop("worker-test")

        self.assertEqual(claim_mock.await_count, 3)
        self.assertEqual(process_mock.await_count, 2)
        self.assertEqual(processed, [1, 2])


if __name__ == "__main__":
    unittest.main()
