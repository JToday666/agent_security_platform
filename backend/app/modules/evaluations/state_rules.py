"""评测任务运行态的状态规则与公共推导。"""

from __future__ import annotations

from datetime import datetime, timezone


TERMINAL_STATUSES = {"completed", "terminated", "canceled", "failed"}


def build_controls(status: str, pause_used: bool) -> dict[str, bool]:
    """根据任务状态生成可执行动作集合。"""
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
    """根据暂停截止时间推导任务应处于的状态。"""
    if status != "paused" or pause_deadline_at is None:
        return status, finalization_reason, pause_deadline_at

    now = datetime.now(timezone.utc)
    deadline = pause_deadline_at.astimezone(timezone.utc)
    if deadline > now:
        return status, finalization_reason, pause_deadline_at

    return "terminated", "auto_terminated_after_pause_timeout", None
