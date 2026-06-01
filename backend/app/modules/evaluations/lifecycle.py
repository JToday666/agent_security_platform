"""评测任务生命周期操作。"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import BenchmarkSample, RiskCategory, RiskSubtype
from app.models.benchmark_run import (
    ExecutionSummary,
    RunDataset,
    RunReport,
    SampleExecution,
    TestRun,
)
from app.modules.difficulty.service import update_sample_difficulty_stats_for_run
from app.modules.evaluations.outcomes import (
    classify_safety_outcome,
    classify_task_outcome,
    normalize_final_label,
    outcome_label_count_key,
    safety_outcome_count_key,
    task_outcome_count_key,
    zero_outcome_axis_counts,
    zero_outcome_label_counts,
)
from app.modules.evaluations.state_rules import TERMINAL_STATUSES, apply_pause_timeout
from app.modules.scoring.service import calculate_and_store_evaluation_score
from app.platform.observability import (
    SampleExecutionEventType,
    record_sample_execution_event,
)

LOGGER = logging.getLogger(__name__)

_FINAL_STATUS_EVENT_TYPES = {
    "completed": SampleExecutionEventType.EVALUATION_COMPLETED,
    "failed": SampleExecutionEventType.EVALUATION_FAILED,
    "canceled": SampleExecutionEventType.EVALUATION_CANCELLED,
    "terminated": SampleExecutionEventType.EVALUATION_TERMINATED,
}


class _CategorySummary(TypedDict):
    categoryId: str
    name: str
    totalSamples: int
    taskCompletedCount: int
    harmDetectedCount: int


class _LevelSummaryBase(TypedDict):
    totalSamples: int
    harmDetectedCount: int


class _LevelSummary(_LevelSummaryBase, total=False):
    level: int


def request_pause(run, now: datetime) -> None:
    """将运行中的任务标记为请求暂停。"""
    run.status = "pausing"
    run.requested_action = "pause"
    run.requested_action_at = now


def mark_run_started(run, now: datetime) -> None:
    """确保任务进入运行态。"""
    if run.started_at is None:
        run.started_at = now
    if run.status == "pending":
        run.status = "running"


def request_resume(run, now: datetime) -> None:
    """恢复暂停中的任务。"""
    run.status = "running"
    run.pause_deadline_at = None
    run.requested_action = None
    run.requested_action_at = now


def pause_after_current_dataset(run, pause_deadline: datetime) -> None:
    """在当前数据集执行完成后将任务切为暂停。"""
    run.status = "paused"
    run.pause_used = True
    run.pause_deadline_at = pause_deadline
    run.requested_action = None
    run.requested_action_at = None


def keep_running(run) -> None:
    """维持任务在运行态。"""
    run.status = "running"


async def request_terminate(db: AsyncSession, run, now: datetime) -> None:
    """请求终止任务，暂停态直接终结。"""
    if run.status == "paused":
        await finalize_run(
            db,
            run,
            final_status="terminated",
            final_reason="terminated_by_user",
            create_report=True,
        )
        return

    run.status = "terminating"
    run.requested_action = "terminate"
    run.requested_action_at = now


async def request_cancel(db: AsyncSession, run, now: datetime) -> None:
    """请求取消任务，待执行或暂停态直接取消。"""
    if run.status in {"pending", "paused"}:
        await finalize_run(
            db,
            run,
            final_status="canceled",
            final_reason="canceled_by_user",
            create_report=False,
        )
        return

    run.status = "canceling"
    run.requested_action = "cancel"
    run.requested_action_at = now


async def finalize_run(
    db: AsyncSession,
    run: TestRun,
    final_status: str,
    final_reason: str,
    create_report: bool,
) -> None:
    """结束评测任务并同步更新关联状态。"""
    now = datetime.now(timezone.utc)
    run.status = final_status
    run.finalization_reason = final_reason
    run.finished_at = now
    run.pause_deadline_at = None
    run.requested_action = None
    run.requested_action_at = None

    datasets = list(
        (
            await db.execute(select(RunDataset).where(RunDataset.run_id == run.id))
        ).scalars()
    )
    for dataset in datasets:
        if dataset.status in TERMINAL_STATUSES:
            continue
        dataset.status = final_status
        dataset.finished_at = dataset.finished_at or now
        dataset.updated_at = now

    if create_report:
        await upsert_report(db, run.id)
        try:
            await update_sample_difficulty_stats_for_run(db, run.id)
            if run.completed_samples > 0:
                await calculate_and_store_evaluation_score(db, run.id)
        except Exception:
            LOGGER.exception(
                "evaluation.finalization_scoring_failed",
                extra={"event": "evaluation.finalization_scoring_failed", "runId": run.id},
            )

    await record_sample_execution_event(
        db,
        run_id=run.id,
        event_type=_FINAL_STATUS_EVENT_TYPES.get(
            final_status, SampleExecutionEventType.EVALUATION_FAILED
        ),
        status=final_status,
        message="Evaluation finalized",
        payload={
            "evaluationId": run.public_id,
            "finalizationReason": final_reason,
            "createReport": create_report,
            "completedSamples": run.completed_samples,
            "totalSamples": run.total_samples,
        },
    )
    await db.commit()


async def mark_run_failed(db: AsyncSession, run: TestRun, final_reason: str) -> None:
    """将评测任务标记为失败。"""
    await finalize_run(
        db,
        run,
        final_status="failed",
        final_reason=final_reason,
        create_report=True,
    )


async def reconcile_run_timeout(db: AsyncSession, run: TestRun) -> bool:
    """处理暂停超时后需要自动收尾的任务。"""
    new_status, new_reason, new_deadline = apply_pause_timeout(
        status=run.status,
        finalization_reason=run.finalization_reason,
        pause_deadline_at=run.pause_deadline_at,
    )
    if (
        new_status == run.status
        and new_reason == run.finalization_reason
        and new_deadline == run.pause_deadline_at
    ):
        return False

    await finalize_run(
        db,
        run,
        final_status=new_status,
        final_reason=new_reason or "auto_terminated_after_pause_timeout",
        create_report=True,
    )
    return True


async def reconcile_expired_paused_runs(db: AsyncSession) -> list[TestRun]:
    """扫描并处理所有超时的暂停任务。"""
    runs = list(
        (
            await db.execute(
                select(TestRun).where(
                    TestRun.status == "paused",
                    TestRun.pause_deadline_at.is_not(None),
                )
            )
        ).scalars()
    )
    reconciled: list[TestRun] = []
    for run in runs:
        changed = await reconcile_run_timeout(db, run)
        if changed:
            reconciled.append(run)
    return reconciled


async def upsert_report(db: AsyncSession, run_id: int) -> RunReport:
    """创建或刷新指定任务的报告记录。"""
    report = (
        await db.execute(select(RunReport).where(RunReport.run_id == run_id))
    ).scalar_one_or_none()
    summary = await build_report_summary(db, run_id)

    if report is None:
        report = RunReport(
            run_id=run_id,
            report_status="available",
            summary_json=summary,
            report_uri=None,
        )
        db.add(report)
    else:
        report.report_status = "available"
        report.summary_json = summary
        report.report_uri = None

    await db.flush()
    return report


async def build_report_summary(db: AsyncSession, run_id: int) -> dict[str, object]:
    """汇总指定任务的评测报告摘要。"""
    run = await db.get(TestRun, run_id)
    summary_rows = (
        await db.execute(
            select(
                RiskCategory.code,
                RiskCategory.name,
                BenchmarkSample.risk_level,
                BenchmarkSample.attack_level,
                SampleExecution.status,
                ExecutionSummary.task_completed,
                ExecutionSummary.harm_detected,
                ExecutionSummary.final_label,
            )
            .join(
                SampleExecution,
                ExecutionSummary.sample_execution_id == SampleExecution.id,
            )
            .join(BenchmarkSample, SampleExecution.sample_id_ref == BenchmarkSample.id)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .join(RiskCategory, RiskSubtype.category_id == RiskCategory.id)
            .where(SampleExecution.run_id == run_id)
        )
    ).all()

    by_category: dict[str, _CategorySummary] = {}
    by_risk_level: defaultdict[int, _LevelSummary] = defaultdict(
        lambda: {"totalSamples": 0, "harmDetectedCount": 0}
    )
    by_attack_level: defaultdict[int, _LevelSummary] = defaultdict(
        lambda: {"totalSamples": 0, "harmDetectedCount": 0}
    )
    task_completed_count = 0
    harm_detected_count = 0
    label_counts = zero_outcome_label_counts()
    axis_counts = zero_outcome_axis_counts()

    for (
        category_code,
        category_name,
        risk_level,
        attack_level,
        execution_status,
        task_completed,
        harm_detected,
        final_label,
    ) in summary_rows:
        outcome_label = normalize_final_label(
            execution_status, task_completed, harm_detected, final_label
        )
        task_outcome = classify_task_outcome(
            execution_status, task_completed, harm_detected, final_label
        )
        safety_outcome = classify_safety_outcome(
            execution_status, task_completed, harm_detected, final_label
        )
        label_count_key = outcome_label_count_key(outcome_label)
        task_count_key = task_outcome_count_key(task_outcome)
        safety_count_key = safety_outcome_count_key(safety_outcome)
        category_stats = by_category.setdefault(
            category_code,
            {
                "categoryId": category_code,
                "name": category_name,
                "totalSamples": 0,
                "taskCompletedCount": 0,
                "harmDetectedCount": 0,
                **zero_outcome_label_counts(),
                **zero_outcome_axis_counts(),
            },
        )
        category_stats["totalSamples"] += 1
        category_stats["taskCompletedCount"] += int(task_completed)
        category_stats["harmDetectedCount"] += int(harm_detected)
        category_stats[label_count_key] += 1
        category_stats[task_count_key] += 1
        category_stats[safety_count_key] += 1

        by_risk_level[risk_level]["level"] = risk_level
        by_risk_level[risk_level]["totalSamples"] += 1
        by_risk_level[risk_level]["harmDetectedCount"] += int(harm_detected)
        by_risk_level[risk_level].setdefault(label_count_key, 0)
        by_risk_level[risk_level][label_count_key] += 1
        by_risk_level[risk_level].setdefault(task_count_key, 0)
        by_risk_level[risk_level][task_count_key] += 1
        by_risk_level[risk_level].setdefault(safety_count_key, 0)
        by_risk_level[risk_level][safety_count_key] += 1

        by_attack_level[attack_level]["level"] = attack_level
        by_attack_level[attack_level]["totalSamples"] += 1
        by_attack_level[attack_level]["harmDetectedCount"] += int(harm_detected)
        by_attack_level[attack_level].setdefault(label_count_key, 0)
        by_attack_level[attack_level][label_count_key] += 1
        by_attack_level[attack_level].setdefault(task_count_key, 0)
        by_attack_level[attack_level][task_count_key] += 1
        by_attack_level[attack_level].setdefault(safety_count_key, 0)
        by_attack_level[attack_level][safety_count_key] += 1

        task_completed_count += int(task_completed)
        harm_detected_count += int(harm_detected)
        label_counts[label_count_key] += 1
        axis_counts[task_count_key] += 1
        axis_counts[safety_count_key] += 1

    return {
        "totalSamples": run.total_samples if run is not None else 0,
        "completedSamples": run.completed_samples if run is not None else 0,
        "taskCompletedCount": task_completed_count,
        "harmDetectedCount": harm_detected_count,
        "pendingReviewCount": label_counts["needsReview"],
        **label_counts,
        **axis_counts,
        "failedCount": run.failed_count if run is not None else 0,
        "byRiskCategory": list(by_category.values()),
        "byRiskLevel": list(by_risk_level.values()),
        "byAttackLevel": list(by_attack_level.values()),
    }
