from __future__ import annotations

from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.response import fail
from app.models.benchmark_run import RunDataset, RunReport, TestRun
from app.models.user import User
from app.schemas.evaluations import EvaluationActionRequest
from app.services.runtime_rules import TERMINAL_STATUSES, apply_pause_timeout, build_controls
from app.services.simulator import finalize_run, schedule_run_processing, upsert_report


class EvaluationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_evaluations(self, current_user: User) -> list[dict[str, object]]:
        rows = list(
            (
                await self.db.execute(
                    select(TestRun)
                    .where(TestRun.user_id == current_user.id)
                    .order_by(TestRun.created_at.desc(), TestRun.id.desc())
                )
            ).scalars()
        )
        items = []
        for run in rows:
            await self._apply_pause_timeout_if_needed(run)
            datasets = await self._load_run_datasets(run.id)
            report = await self._load_run_report(run.id)
            items.append(
                {
                    "evaluationId": run.public_id,
                    "agentName": run.agent_name,
                    "description": run.description,
                    "createdAt": to_zulu(run.created_at),
                    "updatedAt": to_zulu(run.updated_at),
                    "status": run.status,
                    "progressPercent": build_progress_percent(run=run, datasets=datasets),
                    "finalReportAvailable": report is not None and report.report_status == "available",
                    "finalizationReason": run.finalization_reason,
                    "publicToLeaderboard": run.public_to_leaderboard,
                    "datasetIds": [dataset.dataset_code for dataset in datasets],
                    "datasetNames": [dataset.dataset_name for dataset in datasets],
                    "submitMethod": run.submit_method,
                    "score": None,
                    "ownerName": current_user.username,
                    "parameters": build_parameters(run),
                }
            )
        return items

    async def get_evaluation_detail(
        self,
        evaluation_id: str,
        current_user: User,
    ) -> dict[str, object]:
        run = await self._get_run_for_user(evaluation_id=evaluation_id, current_user=current_user)
        return await self._build_detail_snapshot(run=run, owner_name=current_user.username)

    async def apply_action(
        self,
        evaluation_id: str,
        payload: EvaluationActionRequest,
        current_user: User,
        background_tasks: BackgroundTasks | object | None = None,
    ) -> dict[str, object]:
        run = await self._get_run_for_user(evaluation_id=evaluation_id, current_user=current_user)
        owner_name = current_user.username
        now = datetime.now(timezone.utc)

        if payload.action == "pause":
            if run.pause_used:
                raise fail(409, 40902, "该任务已使用过暂停机会，不能再次暂停。")
            if run.status != "running":
                raise fail(409, 40901, "当前状态不允许执行 pause 操作。")
            run.status = "pausing"
            run.requested_action = "pause"
            run.requested_action_at = now
        elif payload.action == "resume":
            if run.status != "paused":
                raise fail(409, 40901, "当前状态不允许执行 resume 操作。")
            run.status = "running"
            run.pause_deadline_at = None
            run.requested_action = None
            run.requested_action_at = now
        elif payload.action == "terminate":
            if run.status not in {"running", "pausing", "paused"}:
                raise fail(409, 40901, "当前状态不允许执行 terminate 操作。")
            if run.status == "paused":
                await finalize_run(self.db, run, final_status="terminated", final_reason="terminated_by_user", create_report=True)
            else:
                run.status = "terminating"
                run.requested_action = "terminate"
                run.requested_action_at = now
        elif payload.action == "cancel":
            if run.status not in {"pending", "running", "pausing", "paused", "terminating", "canceling"}:
                raise fail(409, 40901, "当前状态不允许执行 cancel 操作。")
            if run.status in {"pending", "paused"}:
                await finalize_run(self.db, run, final_status="canceled", final_reason="canceled_by_user", create_report=False)
            else:
                run.status = "canceling"
                run.requested_action = "cancel"
                run.requested_action_at = now
        else:
            raise fail(409, 40901, f"当前状态不允许执行 {payload.action} 操作。")

        await self.db.commit()
        await self.db.refresh(run)
        if payload.action == "resume":
            schedule_run_processing(background_tasks, run.id)
        return await self._build_detail_snapshot(run=run, owner_name=owner_name)

    async def _get_run_for_user(self, evaluation_id: str, current_user: User) -> TestRun:
        run = (
            await self.db.execute(select(TestRun).where(TestRun.public_id == evaluation_id))
        ).scalar_one_or_none()
        if run is None:
            raise fail(404, 40400, "评测记录不存在。")
        if run.user_id != current_user.id:
            raise fail(403, 40300, "无权访问该评测任务。")
        await self._apply_pause_timeout_if_needed(run)
        return run

    async def _apply_pause_timeout_if_needed(self, run: TestRun) -> None:
        new_status, new_reason, new_deadline = apply_pause_timeout(
            status=run.status,
            finalization_reason=run.finalization_reason,
            pause_deadline_at=run.pause_deadline_at,
        )
        if new_status == run.status and new_reason == run.finalization_reason and new_deadline == run.pause_deadline_at:
            return

        await finalize_run(
            self.db,
            run,
            final_status=new_status,
            final_reason=new_reason or "auto_terminated_after_pause_timeout",
            create_report=True,
        )

    async def _load_run_datasets(self, run_id: int) -> list[RunDataset]:
        return list(
            (
                await self.db.execute(
                    select(RunDataset)
                    .where(RunDataset.run_id == run_id)
                    .order_by(RunDataset.order_no.asc(), RunDataset.id.asc())
                )
            ).scalars()
        )

    async def _load_run_report(self, run_id: int) -> RunReport | None:
        return (
            await self.db.execute(select(RunReport).where(RunReport.run_id == run_id))
        ).scalar_one_or_none()

    async def _build_detail_snapshot(self, run: TestRun, owner_name: str) -> dict[str, object]:
        datasets = await self._load_run_datasets(run.id)
        report = await self._load_run_report(run.id)
        running_dataset = next(
            (dataset for dataset in datasets if dataset.status == "running"),
            None,
        )
        completed_dataset_count = sum(int(dataset.status in TERMINAL_STATUSES) for dataset in datasets)
        final_report_available = report is not None and report.report_status == "available"
        return {
            "evaluationId": run.public_id,
            "agentName": run.agent_name,
            "description": run.description,
            "createdAt": to_zulu(run.created_at),
            "updatedAt": to_zulu(run.updated_at),
            "status": run.status,
            "score": None,
            "publicToLeaderboard": run.public_to_leaderboard,
            "datasetIds": [dataset.dataset_code for dataset in datasets],
            "datasetNames": [dataset.dataset_name for dataset in datasets],
            "submitMethod": run.submit_method,
            "ownerName": owner_name,
            "parameters": build_parameters(run),
            "progress": {
                "percent": build_progress_percent(run=run, datasets=datasets),
                "totalDatasetCount": len(datasets),
                "completedDatasetCount": completed_dataset_count,
                "runningDatasetId": None if running_dataset is None else running_dataset.dataset_code,
                "runningDatasetName": None if running_dataset is None else running_dataset.dataset_name,
                "pauseDeadlineAt": None if run.pause_deadline_at is None else to_zulu(run.pause_deadline_at),
                "statusText": build_status_text(
                    status=run.status,
                    running_dataset_name=None if running_dataset is None else running_dataset.dataset_name,
                ),
            },
            "controls": build_controls(status=run.status, pause_used=run.pause_used),
            "finalReportAvailable": final_report_available,
            "finalizationReason": run.finalization_reason,
            "report": None if not final_report_available else build_report_payload(report),
        }


def build_parameters(run: TestRun) -> dict[str, object]:
    return run.execution_config.get(
        "parameters",
        {"difficulty": 0.5, "timeoutMinutes": 15, "retryEnabled": False},
    )


def build_progress_percent(run: TestRun, datasets: list[RunDataset]) -> int:
    if run.total_samples > 0:
        return max(0, min(100, round((run.completed_samples / run.total_samples) * 100)))
    if not datasets:
        return 0
    completed = sum(int(dataset.status in TERMINAL_STATUSES) for dataset in datasets)
    return max(0, min(100, round((completed / len(datasets)) * 100)))


def build_status_text(status: str, running_dataset_name: str | None) -> str:
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


def build_report_payload(report: RunReport) -> dict[str, object]:
    return {
        "reportStatus": report.report_status,
        "summary": report.summary_json or {
            "totalSamples": 0,
            "completedSamples": 0,
            "taskCompletedCount": 0,
            "harmDetectedCount": 0,
            "failedCount": 0,
            "byRiskCategory": [],
            "byRiskLevel": [],
            "byAttackLevel": [],
        },
        "reportUri": report.report_uri,
    }


def to_zulu(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
