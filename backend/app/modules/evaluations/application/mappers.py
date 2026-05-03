"""Evaluation response mapping helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.evaluations.state_rules import TERMINAL_STATUSES


def to_zulu(value: datetime) -> str:
    """Format datetimes for public API responses."""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_parameters(run) -> dict[str, object]:
    """Expose saved execution parameters with legacy defaults."""
    return run.execution_config.get(
        "parameters",
        {"difficulty": 0.5, "timeoutMinutes": 15, "retryEnabled": False},
    )


def build_progress_percent(run, datasets: list) -> int:
    """Calculate evaluation progress for list/detail responses."""
    if run.total_samples > 0:
        return max(0, min(100, round((run.completed_samples / run.total_samples) * 100)))
    if not datasets:
        return 0
    completed = sum(int(dataset.status in TERMINAL_STATUSES) for dataset in datasets)
    return max(0, min(100, round((completed / len(datasets)) * 100)))


def build_status_text(status: str, running_dataset_name: str | None) -> str:
    """Build frontend-facing status text."""
    if status == "pending":
        return "任务已创建，等待开始评测。"
    if status == "running":
        if running_dataset_name is None:
            return "任务正在评测中。"
        return f"当前正在评测数据集 {running_dataset_name}。"
    if status == "pausing":
        return "当前数据集完成后任务将进入暂停状态。"
    if status == "paused":
        return "任务已暂停，请在截止时间前恢复。"
    if status == "terminating":
        return "当前数据集完成后任务将终止并生成报告。"
    if status == "canceling":
        return "任务正在取消，请稍候。"
    if status == "completed":
        return "评测已完成。"
    if status == "terminated":
        return "评测已终止。"
    if status == "canceled":
        return "评测已取消。"
    return "评测执行失败。"


def build_report_payload(report) -> dict[str, object]:
    """Map report rows to the public detail payload."""
    return {
        "reportStatus": report.report_status,
        "summary": report.summary_json
        or {
            "totalSamples": 0,
            "completedSamples": 0,
            "taskCompletedCount": 0,
            "harmDetectedCount": 0,
            "pendingReviewCount": 0,
            "failedCount": 0,
            "byRiskCategory": [],
            "byRiskLevel": [],
            "byAttackLevel": [],
        },
        "reportUri": report.report_uri,
    }

