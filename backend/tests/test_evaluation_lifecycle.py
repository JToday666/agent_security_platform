from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.modules.evaluations import lifecycle


class EvaluationLifecycleTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_request_pause_marks_running_run_as_pausing(self) -> None:
        now = datetime.now(timezone.utc)
        run = SimpleNamespace(
            status="running",
            pause_used=False,
            requested_action=None,
            requested_action_at=None,
        )

        lifecycle.request_pause(run, now)

        self.assertEqual(run.status, "pausing")
        self.assertEqual(run.requested_action, "pause")
        self.assertEqual(run.requested_action_at, now)

    async def test_request_resume_clears_pause_and_claim_fields(self) -> None:
        now = datetime.now(timezone.utc)
        run = SimpleNamespace(
            status="paused",
            pause_deadline_at=now,
            requested_action="pause",
            requested_action_at=None,
            claimed_by="worker-1",
            claimed_at=now,
            claim_heartbeat_at=now,
        )

        lifecycle.request_resume(run, now)

        self.assertEqual(run.status, "running")
        self.assertIsNone(run.pause_deadline_at)
        self.assertIsNone(run.requested_action)
        self.assertEqual(run.requested_action_at, now)
        self.assertIsNone(run.claimed_by)
        self.assertIsNone(run.claimed_at)
        self.assertIsNone(run.claim_heartbeat_at)

    async def test_request_cancel_finalizes_paused_run_immediately(self) -> None:
        now = datetime.now(timezone.utc)
        db = AsyncMock()
        run = SimpleNamespace(status="paused")

        with patch.object(lifecycle, "finalize_run", new=AsyncMock()) as finalize_mock:
            await lifecycle.request_cancel(db, run, now)

        finalize_mock.assert_awaited_once_with(
            db,
            run,
            final_status="canceled",
            final_reason="canceled_by_user",
            create_report=False,
        )

    async def test_reconcile_run_timeout_delegates_to_finalize_when_expired(self) -> None:
        db = AsyncMock()
        run = SimpleNamespace(
            status="paused",
            finalization_reason=None,
            pause_deadline_at=datetime.now(timezone.utc),
        )

        with patch.object(
            lifecycle,
            "apply_pause_timeout",
            return_value=("terminated", "auto_terminated_after_pause_timeout", None),
        ), patch.object(lifecycle, "finalize_run", new=AsyncMock()) as finalize_mock:
            changed = await lifecycle.reconcile_run_timeout(db, run)

        self.assertTrue(changed)
        finalize_mock.assert_awaited_once_with(
            db,
            run,
            final_status="terminated",
            final_reason="auto_terminated_after_pause_timeout",
            create_report=True,
        )

    async def test_build_report_summary_counts_pending_review(self) -> None:
        class FakeResult:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows

        db = AsyncMock()
        db.get = AsyncMock(
            return_value=SimpleNamespace(
                total_samples=3,
                completed_samples=2,
                failed_count=1,
            )
        )
        db.execute = AsyncMock(
            return_value=FakeResult(
                [
                    ("cat", "Category", 1, 1, False, False, "needs_review"),
                    ("cat", "Category", 1, 1, True, False, "safe"),
                ]
            )
        )

        summary = await lifecycle.build_report_summary(db, 1)

        self.assertEqual(summary["pendingReviewCount"], 1)
        self.assertEqual(summary["taskCompletedCount"], 1)
        self.assertEqual(summary["harmDetectedCount"], 0)


if __name__ == "__main__":
    unittest.main()
