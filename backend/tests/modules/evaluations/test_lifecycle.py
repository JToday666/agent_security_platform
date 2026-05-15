from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.evaluations import lifecycle


@pytest.mark.asyncio
async def test_request_pause_marks_running_run_as_pausing() -> None:
    now = datetime.now(timezone.utc)
    run = SimpleNamespace(
        status="running",
        pause_used=False,
        requested_action=None,
        requested_action_at=None,
    )

    lifecycle.request_pause(run, now)

    assert run.status == "pausing"
    assert run.requested_action == "pause"
    assert run.requested_action_at == now


@pytest.mark.asyncio
async def test_request_resume_clears_pause_and_claim_fields() -> None:
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

    assert run.status == "running"
    assert run.pause_deadline_at is None
    assert run.requested_action is None
    assert run.requested_action_at == now
    assert run.claimed_by is None
    assert run.claimed_at is None
    assert run.claim_heartbeat_at is None


@pytest.mark.asyncio
async def test_request_cancel_finalizes_paused_run_immediately() -> None:
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


@pytest.mark.asyncio
async def test_reconcile_run_timeout_delegates_to_finalize_when_expired() -> None:
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

    assert changed is True
    finalize_mock.assert_awaited_once_with(
        db,
        run,
        final_status="terminated",
        final_reason="auto_terminated_after_pause_timeout",
        create_report=True,
    )


@pytest.mark.asyncio
async def test_build_report_summary_counts_pending_review() -> None:
    class FakeResult:
        def __init__(self, rows):
            self._rows = rows

        def all(self):
            return self._rows

    db = AsyncMock()
    db.get = AsyncMock(
        return_value=SimpleNamespace(
            total_samples=3, completed_samples=2, failed_count=1
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

    assert summary["pendingReviewCount"] == 1
    assert summary["taskCompletedCount"] == 1
    assert summary["harmDetectedCount"] == 0
