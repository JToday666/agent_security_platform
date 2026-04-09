from __future__ import annotations

from datetime import datetime, timezone


TERMINAL_STATUSES = {"completed", "terminated", "canceled", "failed"}


def is_valid_request_id(value: str) -> bool:
    if not (6 <= len(value) <= 128):
        return False
    if not value[0].isalnum():
        return False
    return all(char.isalnum() or char in {"_", "-"} for char in value)


def difficulty_bucket_bounds(difficulty: float) -> tuple[float, float, bool]:
    lower = max(0.0, round(difficulty - 0.05, 2))
    upper = min(1.0, round(difficulty + 0.05, 2))
    include_upper = upper == 1.0
    return lower, upper, include_upper


def build_controls(status: str, pause_used: bool) -> dict[str, bool]:
    can_pause = status == "running" and not pause_used
    can_resume = status == "paused"
    can_terminate = status in {"running", "pausing", "paused"}
    can_cancel = status in {"pending", "running", "pausing", "paused", "terminating", "canceling"}
    return {
        "canPause": can_pause,
        "canResume": can_resume,
        "canTerminate": can_terminate,
        "canCancel": can_cancel,
        "pauseUsed": pause_used,
    }


def apply_pause_timeout(
    status: str,
    finalization_reason: str | None,
    pause_deadline_at: datetime | None,
) -> tuple[str, str | None, datetime | None]:
    if status != "paused" or pause_deadline_at is None:
        return status, finalization_reason, pause_deadline_at

    now = datetime.now(timezone.utc)
    deadline = pause_deadline_at.astimezone(timezone.utc)
    if deadline > now:
        return status, finalization_reason, pause_deadline_at

    return "terminated", "auto_terminated_after_pause_timeout", None
