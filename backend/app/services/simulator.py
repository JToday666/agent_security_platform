from __future__ import annotations

import asyncio
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import BackgroundTasks
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.benchmark import BenchmarkSample, RiskCategory, RiskSubtype, SampleOracle
from app.models.benchmark_run import (
    ExecutionSummary,
    OracleResult,
    RunDataset,
    RunReport,
    RunSample,
    SampleExecution,
    TestRun,
)
from app.services.runtime_rules import TERMINAL_STATUSES

RUNNER_TASKS: dict[int, asyncio.Task[None]] = {}


def schedule_run_processing(background_tasks: BackgroundTasks | object | None, run_id: int) -> None:
    if background_tasks is not None and hasattr(background_tasks, "add_task"):
        background_tasks.add_task(start_run_processing, run_id)


async def start_run_processing(run_id: int) -> None:
    task = RUNNER_TASKS.get(run_id)
    if task is not None and not task.done():
        return

    task = asyncio.create_task(process_run(run_id))
    RUNNER_TASKS[run_id] = task


async def process_run(run_id: int) -> None:
    try:
        async with AsyncSessionLocal() as db:
            while True:
                run = await db.get(TestRun, run_id)
                if run is None or run.status in TERMINAL_STATUSES:
                    break

                if run.requested_action == "cancel" and run.status in {"pending", "canceling"}:
                    await finalize_run(db, run, final_status="canceled", final_reason="canceled_by_user", create_report=False)
                    break

                datasets = list(
                    (
                        await db.execute(
                            select(RunDataset)
                            .where(RunDataset.run_id == run.id)
                            .order_by(RunDataset.order_no.asc(), RunDataset.id.asc())
                        )
                    ).scalars()
                )

                pending_datasets = [dataset for dataset in datasets if dataset.status not in TERMINAL_STATUSES]
                if not pending_datasets:
                    await finalize_run(db, run, final_status="completed", final_reason="completed", create_report=True)
                    break

                current_dataset = pending_datasets[0]
                now = datetime.now(timezone.utc)
                if run.started_at is None:
                    run.started_at = now
                if run.status == "pending":
                    run.status = "running"

                if current_dataset.total_samples == 0:
                    current_dataset.status = "completed"
                    current_dataset.started_at = current_dataset.started_at or now
                    current_dataset.finished_at = now
                    current_dataset.updated_at = now
                    await db.commit()
                    continue

                current_dataset.status = "running"
                current_dataset.started_at = current_dataset.started_at or now
                current_dataset.updated_at = now
                await db.commit()

                await asyncio.sleep(settings.SIMULATED_DATASET_STEP_SECONDS)

                await db.refresh(run)
                await db.refresh(current_dataset)
                await complete_dataset(db, run, current_dataset)
                await db.refresh(run)

                if run.requested_action == "cancel":
                    await finalize_run(db, run, final_status="canceled", final_reason="canceled_by_user", create_report=False)
                    break

                if run.requested_action == "pause":
                    pause_deadline = datetime.now(timezone.utc) + timedelta(minutes=settings.PAUSE_TIMEOUT_MINUTES)
                    run.status = "paused"
                    run.pause_used = True
                    run.pause_deadline_at = pause_deadline
                    run.requested_action = None
                    run.requested_action_at = None
                    await db.commit()
                    break

                if run.requested_action == "terminate":
                    await finalize_run(db, run, final_status="terminated", final_reason="terminated_by_user", create_report=True)
                    break

                datasets = list(
                    (
                        await db.execute(
                            select(RunDataset)
                            .where(RunDataset.run_id == run.id)
                            .order_by(RunDataset.order_no.asc(), RunDataset.id.asc())
                        )
                    ).scalars()
                )
                if all(dataset.status in TERMINAL_STATUSES for dataset in datasets):
                    await finalize_run(db, run, final_status="completed", final_reason="completed", create_report=True)
                    break

                run.status = "running"
                await db.commit()
    finally:
        RUNNER_TASKS.pop(run_id, None)


async def complete_dataset(db, run: TestRun, dataset: RunDataset) -> None:
    rows = (
        await db.execute(
            select(RunSample, BenchmarkSample)
            .join(BenchmarkSample, RunSample.sample_id_ref == BenchmarkSample.id)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(RunSample.run_id == run.id, RiskSubtype.code == dataset.dataset_code)
            .order_by(RunSample.order_no.asc(), RunSample.id.asc())
        )
    ).all()

    completed = 0
    now = datetime.now(timezone.utc)
    for run_sample, sample in rows:
        execution = (
            await db.execute(
                select(SampleExecution).where(
                    SampleExecution.run_sample_id == run_sample.id,
                    SampleExecution.retry_no == 0,
                )
            )
        ).scalar_one()

        if execution.status == "done":
            completed += 1
            continue

        execution.status = "executing"
        execution.started_at = execution.started_at or now
        await db.flush()

        harm_detected, task_completed = deterministic_sample_outcome(run.id, sample.id)
        execution.status = "done"
        execution.finished_at = datetime.now(timezone.utc)
        execution.updated_at = execution.finished_at

        db.add(
            ExecutionSummary(
                sample_execution_id=execution.id,
                task_completed=task_completed,
                harm_detected=harm_detected,
                summary_text="模拟联调执行结果",
                final_label=build_final_label(task_completed=task_completed, harm_detected=harm_detected),
            )
        )

        oracles = list(
            (
                await db.execute(
                    select(SampleOracle).where(
                        SampleOracle.sample_id_ref == sample.id,
                        SampleOracle.is_active.is_(True),
                    )
                )
            ).scalars()
        )
        for oracle in oracles:
            matched = task_completed and not harm_detected if oracle.oracle_kind == 1 else harm_detected
            db.add(
                OracleResult(
                    sample_execution_id=execution.id,
                    oracle_id=oracle.id,
                    matched=matched,
                    score=Decimal("1.000") if matched else Decimal("0.000"),
                    evidence_summary="模拟联调证据摘要",
                    evidence_ref={"source": "simulator", "oracleKind": oracle.oracle_kind},
                    evaluator_version="simulator-v1",
                )
            )

        run.completed_samples += 1
        run.success_count += 1
        completed += 1

    dataset.completed_samples = completed
    dataset.status = "completed"
    dataset.finished_at = datetime.now(timezone.utc)
    dataset.updated_at = dataset.finished_at
    await db.commit()


def deterministic_sample_outcome(run_id: int, sample_id: int) -> tuple[bool, bool]:
    digest = hashlib.sha1(f"{run_id}:{sample_id}".encode("utf-8")).hexdigest()
    seed = int(digest[:8], 16)
    harm_detected = seed % 5 == 0
    task_completed = seed % 7 != 0
    return harm_detected, task_completed


def build_final_label(task_completed: bool, harm_detected: bool) -> str:
    if harm_detected:
        return "hijacked"
    if task_completed:
        return "safe"
    return "refused"


async def finalize_run(db, run: TestRun, final_status: str, final_reason: str, create_report: bool) -> None:
    now = datetime.now(timezone.utc)
    run.status = final_status
    run.finalization_reason = final_reason
    run.finished_at = now
    run.pause_deadline_at = None
    run.requested_action = None
    run.requested_action_at = None

    datasets = list(
        (
            await db.execute(
                select(RunDataset).where(RunDataset.run_id == run.id)
            )
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

    await db.commit()


async def upsert_report(db, run_id: int) -> RunReport:
    report = (
        await db.execute(select(RunReport).where(RunReport.run_id == run_id))
    ).scalar_one_or_none()
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


async def build_report_summary(db, run_id: int) -> dict[str, object]:
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
