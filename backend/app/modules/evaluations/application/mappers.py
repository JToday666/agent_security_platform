"""Evaluation response mapping helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.evaluations.state_rules import TERMINAL_STATUSES
from app.platform.i18n import translate


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
        return max(
            0, min(100, round((run.completed_samples / run.total_samples) * 100))
        )
    if not datasets:
        return 0
    completed = sum(int(dataset.status in TERMINAL_STATUSES) for dataset in datasets)
    return max(0, min(100, round((completed / len(datasets)) * 100)))


def build_status_text(status: str, running_dataset_name: str | None) -> str:
    """Build frontend-facing status text."""
    if status == "pending":
        return translate("evaluations.status.pending")
    if status == "running":
        if running_dataset_name is None:
            return translate("evaluations.status.running")
        return translate(
            "evaluations.status.running_dataset", {"datasetName": running_dataset_name}
        )
    if status == "pausing":
        return translate("evaluations.status.pausing")
    if status == "paused":
        return translate("evaluations.status.paused")
    if status == "terminating":
        return translate("evaluations.status.terminating")
    if status == "canceling":
        return translate("evaluations.status.canceling")
    if status == "completed":
        return translate("evaluations.status.completed")
    if status == "terminated":
        return translate("evaluations.status.terminated")
    if status == "canceled":
        return translate("evaluations.status.canceled")
    return translate("evaluations.status.failed")


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
