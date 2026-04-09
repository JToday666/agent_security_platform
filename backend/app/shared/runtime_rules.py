"""评测任务运行状态和规则相关的公共函数。"""

from __future__ import annotations

from datetime import datetime, timezone


TERMINAL_STATUSES = {"completed", "terminated", "canceled", "failed"}


def is_valid_request_id(value: str) -> bool:
    """校验外部传入的请求编号格式。"""
    if not (6 <= len(value) <= 128):
        return False
    if not value[0].isalnum():
        return False
    return all(char.isalnum() or char in {"_", "-"} for char in value)


def difficulty_bucket_bounds(difficulty: float) -> tuple[float, float, bool]:
    """返回难度值对应的样本筛选区间。"""
    lower = max(0.0, round(difficulty - 0.05, 2))
    upper = min(1.0, round(difficulty + 0.05, 2))
    include_upper = upper == 1.0
    return lower, upper, include_upper


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
