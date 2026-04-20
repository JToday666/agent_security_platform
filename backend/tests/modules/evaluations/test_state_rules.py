from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.evaluations.state_rules import TERMINAL_STATUSES, apply_pause_timeout, build_controls


def test_terminal_statuses_are_defined_for_run_domain() -> None:
    assert TERMINAL_STATUSES == {"completed", "terminated", "canceled", "failed"}


def test_build_controls_for_running_and_paused_states() -> None:
    assert build_controls(status="running", pause_used=False) == {
        "canPause": True,
        "canResume": False,
        "canTerminate": True,
        "canCancel": True,
        "pauseUsed": False,
    }
    assert build_controls(status="paused", pause_used=True) == {
        "canPause": False,
        "canResume": True,
        "canTerminate": True,
        "canCancel": True,
        "pauseUsed": True,
    }


def test_apply_pause_timeout_auto_terminates_expired_paused_run() -> None:
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    status, finalization_reason, pause_deadline_at = apply_pause_timeout(
        status="paused",
        finalization_reason=None,
        pause_deadline_at=expired_at,
    )

    assert status == "terminated"
    assert finalization_reason == "auto_terminated_after_pause_timeout"
    assert pause_deadline_at is None


def test_apply_pause_timeout_keeps_active_runs_unchanged() -> None:
    future_at = datetime.now(timezone.utc) + timedelta(minutes=1)

    status, finalization_reason, pause_deadline_at = apply_pause_timeout(
        status="running",
        finalization_reason=None,
        pause_deadline_at=future_at,
    )

    assert status == "running"
    assert finalization_reason is None
    assert pause_deadline_at == future_at
