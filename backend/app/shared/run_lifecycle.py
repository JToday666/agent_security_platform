from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.benchmark import BenchmarkSample, RiskCategory, RiskSubtype
from app.models.benchmark_run import ExecutionSummary, RunDataset, RunReport, SampleExecution, TestRun
from app.shared.runtime_rules import TERMINAL_STATUSES, apply_pause_timeout


async def finalize_run(
    db: AsyncSession,
    run: TestRun,
    final_status: str,
    final_reason: str,
    create_report: bool,
) -> None:
    now = datetime.now(timezone.utc)
    run.status = final_status
    run.finalization_reason = final_reason
    run.finished_at = now
    run.pause_deadline_at = None
    run.requested_action = None
    run.requested_action_at = None
    run.claimed_by = None
    run.claimed_at = None
    run.claim_heartbeat_at = None

    datasets = list((await db.execute(select(RunDataset).where(RunDataset.run_id == run.id))).scalars())
    for dataset in datasets:
        if dataset.status in TERMINAL_STATUSES:
            continue
        dataset.status = final_status
        dataset.finished_at = dataset.finished_at or now
        dataset.updated_at = now

    if create_report:
        await upsert_report(db, run.id)

    await db.commit()


async def mark_run_failed(db: AsyncSession, run: TestRun, final_reason: str) -> None:
    await finalize_run(
        db,
        run,
        final_status="failed",
        final_reason=final_reason,
        create_report=True,
    )


async def reconcile_run_timeout(db: AsyncSession, run: TestRun) -> bool:
    new_status, new_reason, new_deadline = apply_pause_timeout(
        status=run.status,
        finalization_reason=run.finalization_reason,
        pause_deadline_at=run.pause_deadline_at,
    )
    if new_status == run.status and new_reason == run.finalization_reason and new_deadline == run.pause_deadline_at:
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
    report = (await db.execute(select(RunReport).where(RunReport.run_id == run_id))).scalar_one_or_none()
    summary = await build_report_summary(db, run_id)

    if report is None:
        report = RunReport(run_id=run_id, report_status="available", summary_json=summary, report_uri=None)
        db.add(report)
    else:
        report.report_status = "available"
        report.summary_json = summary
        report.report_uri = None

    await db.flush()
    return report


async def build_report_summary(db: AsyncSession, run_id: int) -> dict[str, object]:
    run = await db.get(TestRun, run_id)
    summary_rows = (
        await db.execute(
            select(
                RiskCategory.code,
                RiskCategory.name,
                BenchmarkSample.risk_level,
                BenchmarkSample.attack_level,
                ExecutionSummary.task_completed,
                ExecutionSummary.harm_detected,
            )
            .join(SampleExecution, ExecutionSummary.sample_execution_id == SampleExecution.id)
            .join(BenchmarkSample, SampleExecution.sample_id_ref == BenchmarkSample.id)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .join(RiskCategory, RiskSubtype.category_id == RiskCategory.id)
            .where(SampleExecution.run_id == run_id)
        )
    ).all()

    by_category: dict[str, dict[str, object]] = {}
    by_risk_level: dict[int, dict[str, object]] = defaultdict(lambda: {"totalSamples": 0, "harmDetectedCount": 0})
    by_attack_level: dict[int, dict[str, object]] = defaultdict(lambda: {"totalSamples": 0, "harmDetectedCount": 0})
    task_completed_count = 0
    harm_detected_count = 0

    for category_code, category_name, risk_level, attack_level, task_completed, harm_detected in summary_rows:
        category_stats = by_category.setdefault(
            category_code,
            {
                "categoryId": category_code,
                "name": category_name,
                "totalSamples": 0,
                "taskCompletedCount": 0,
                "harmDetectedCount": 0,
            },
        )
        category_stats["totalSamples"] += 1
        category_stats["taskCompletedCount"] += int(task_completed)
        category_stats["harmDetectedCount"] += int(harm_detected)

        by_risk_level[risk_level]["level"] = risk_level
        by_risk_level[risk_level]["totalSamples"] += 1
        by_risk_level[risk_level]["harmDetectedCount"] += int(harm_detected)

        by_attack_level[attack_level]["level"] = attack_level
        by_attack_level[attack_level]["totalSamples"] += 1
        by_attack_level[attack_level]["harmDetectedCount"] += int(harm_detected)

        task_completed_count += int(task_completed)
        harm_detected_count += int(harm_detected)

    return {
        "totalSamples": run.total_samples if run is not None else 0,
        "completedSamples": run.completed_samples if run is not None else 0,
        "taskCompletedCount": task_completed_count,
        "harmDetectedCount": harm_detected_count,
        "failedCount": run.failed_count if run is not None else 0,
        "byRiskCategory": list(by_category.values()),
        "byRiskLevel": list(by_risk_level.values()),
        "byAttackLevel": list(by_attack_level.values()),
    }
