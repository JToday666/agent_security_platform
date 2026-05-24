"""评测任务模块服务，负责列表、详情与任务动作编排。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.models.benchmark_run import TestRun
from app.modules.agents.application.mappers import (
    runtime_snapshot as agent_runtime_snapshot,
)
from app.modules.evaluations import lifecycle
from app.modules.evaluations.application.ids import (
    generate_public_id,
    request_fingerprint,
)
from app.modules.evaluations.application.mappers import (
    build_parameters,
    build_progress_percent,
    build_report_payload,
    build_status_text,
    to_zulu,
)
from app.modules.evaluations.application.validation import (
    invalid_evaluation,
    validate_submission_payload,
)
from app.modules.evaluations.domain.constants import (
    DIFFICULTY_META,
    MAX_STEPS_META,
    TIMEOUT_META,
)
from app.modules.evaluations.repository import EvaluationRepository
from app.modules.evaluations.schemas import (
    EvaluationActionRequest,
    EvaluationCreateRequest,
    EvaluationCreateResponse,
    EvaluationDetail,
    EvaluationListItem,
    EvaluationReportPayload,
    EvaluationSubmitMeta,
    EvaluationValidateResponse,
)
from app.modules.evaluations.state_rules import TERMINAL_STATUSES, build_controls
from app.platform.errors import ConflictError, ForbiddenError, NotFoundError
from app.platform.i18n import DEFAULT_LOCALE, get_current_locale


DIFFICULTY_BUCKETS = ("0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0")


def _as_float(value: Decimal | float | int | None) -> float:
    """Convert numeric ORM values to JSON-friendly floats."""
    if value is None:
        return 0.0
    return float(value)


def _zero_counts() -> dict[str, int]:
    return {"total": 0, "success": 0, "failed": 0, "error": 0}


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _bucket_index(difficulty: float) -> int:
    value = max(0.0, min(1.0, difficulty))
    return min(int(value * len(DIFFICULTY_BUCKETS)), len(DIFFICULTY_BUCKETS) - 1)


def _duration_ms(started_at: datetime | None, finished_at: datetime | None) -> int:
    if started_at is None or finished_at is None:
        return 0
    return max(0, round((finished_at - started_at).total_seconds() * 1000))


def _classify_report_outcome(
    status: str,
    task_completed: bool | None,
    harm_detected: bool | None,
    final_label: str | None,
) -> str:
    if status == "error" or task_completed is None or final_label == "needs_review":
        return "error"
    if task_completed is True and harm_detected is False:
        return "success"
    return "failed"


class EvaluationService:
    """封装评测任务查询与动作处理能力。"""

    def __init__(self, repository: EvaluationRepository) -> None:
        """绑定任务查询与动作处理共用的仓储实例。"""
        self.repository = repository

    async def get_submit_meta(self) -> EvaluationSubmitMeta:
        """返回新评测提交页元数据。"""
        return EvaluationSubmitMeta.model_validate(
            {
                "submitMethods": ["api"],
                "difficulty": DIFFICULTY_META,
                "timeoutMinutes": TIMEOUT_META,
                "maxSteps": MAX_STEPS_META,
                "publicToLeaderboard": {"default": True},
                "leaderboardDisplayMode": {
                    "default": "public",
                    "options": ["public", "anonymous"],
                },
            }
        )

    async def validate_submission(
        self, payload: EvaluationCreateRequest, current_user
    ) -> EvaluationValidateResponse:
        """校验评测提交请求。"""
        warnings, _selection, _agent = await validate_submission_payload(
            self.repository, payload, current_user
        )
        response_warnings: list[dict[str, str] | str] = list(warnings)
        return EvaluationValidateResponse(ok=True, warnings=response_warnings)

    async def create_evaluation(
        self, payload: EvaluationCreateRequest, current_user
    ) -> EvaluationCreateResponse:
        """创建评测任务并冻结 Agent 配置。"""
        fingerprint = request_fingerprint(payload)
        existing = await self.repository.get_existing_run(
            current_user.id, payload.request_id
        )
        if existing is not None:
            if existing.sample_query_snapshot.get("requestBodyHash") != fingerprint:
                raise ConflictError(
                    "requestId 已被不同请求体使用。",
                    code=40900,
                    message_key="errors.evaluations.request_body_conflict",
                )
            return EvaluationCreateResponse(
                evaluation_id=existing.public_id,
                submit_method=existing.submit_method,
                agent_id=str(
                    existing.execution_config.get("agentId") or payload.agent_id
                ),
                status=existing.status,
                created_at=to_zulu(existing.created_at),
            )

        warnings, selection, agent = await validate_submission_payload(
            self.repository, payload, current_user
        )
        public_id = generate_public_id()
        now = datetime.now(timezone.utc)
        frozen_agent_snapshot = agent_runtime_snapshot(agent)
        parameter_snapshot = {
            "difficulty": payload.parameters.difficulty,
            "timeoutMinutes": payload.parameters.timeout_minutes,
            "maxSteps": payload.parameters.max_steps,
            "retryEnabled": False,
        }
        run = TestRun(
            user_id=current_user.id,
            public_id=public_id,
            agent_name=agent.name,
            description=agent.description,
            submit_method="api",
            public_to_leaderboard=True,
            leaderboard_display_mode=payload.leaderboard_display_mode,
            request_id=payload.request_id,
            agent_base_url=str(agent.connection["baseUrl"]),
            credential_ref=agent.credential_ref,
            status="pending",
            sample_query_snapshot={
                "datasetIds": selection["dataset_ids"],
                "difficulty": payload.parameters.difficulty,
                "matchedSampleCount": len(selection["sample_rows"]),
                "matchedDatasetCount": len(selection["dataset_ids"]),
                "warnings": warnings,
                "requestBodyHash": fingerprint,
                "agentId": agent.public_id,
            },
            execution_config={
                "parameters": parameter_snapshot,
                "agentId": agent.public_id,
                "frozenAgentSnapshot": frozen_agent_snapshot,
                "dispatch": {"mode": "external_agent_api"},
            },
            total_samples=len(selection["sample_rows"]),
            completed_samples=0,
            success_count=0,
            failed_count=0,
            created_at=now,
            updated_at=now,
            claimed_by=None,
            claimed_at=None,
            claim_heartbeat_at=None,
        )
        try:
            run = await self.repository.create_run_graph(
                run=run,
                dataset_ids=selection["dataset_ids"],
                dataset_names=selection["dataset_names"],
                matched_counts=selection["matched_counts"],
                sample_rows=selection["sample_rows"],
            )
            await self.repository.commit()
        except IntegrityError as exc:
            await self.repository.rollback()
            existing = await self.repository.get_existing_run(
                current_user.id, payload.request_id
            )
            if (
                existing is not None
                and existing.sample_query_snapshot.get("requestBodyHash") == fingerprint
            ):
                return EvaluationCreateResponse(
                    evaluation_id=existing.public_id,
                    submit_method=existing.submit_method,
                    agent_id=str(
                        existing.execution_config.get("agentId") or payload.agent_id
                    ),
                    status=existing.status,
                    created_at=to_zulu(existing.created_at),
                )
            raise exc
        except Exception:
            await self.repository.rollback()
            raise

        return EvaluationCreateResponse(
            evaluation_id=run.public_id,
            submit_method=run.submit_method,
            agent_id=agent.public_id,
            status=run.status,
            created_at=to_zulu(run.created_at),
        )

    async def list_evaluations(self, current_user) -> list[EvaluationListItem]:
        """返回当前用户的评测任务列表。"""
        runs = await self.repository.list_runs_for_user(current_user.id)
        datasets_by_run, reports_by_run = await self.repository.load_related_for_runs(
            [run.id for run in runs]
        )
        dataset_names = await self._localized_dataset_names(
            [
                dataset
                for datasets in datasets_by_run.values()
                for dataset in datasets
            ]
        )
        scores_by_run = {}
        if hasattr(self.repository, "load_scores_for_runs"):
            scores_by_run = await self.repository.load_scores_for_runs(
                [run.id for run in runs]
            )
        items: list[EvaluationListItem] = []
        for run in runs:
            datasets = datasets_by_run.get(run.id, [])
            report = reports_by_run.get(run.id)
            score = scores_by_run.get(run.id)
            items.append(
                EvaluationListItem.model_validate(
                    {
                        "evaluationId": run.public_id,
                        "agentName": run.agent_name,
                        "description": run.description,
                        "createdAt": to_zulu(run.created_at),
                        "updatedAt": to_zulu(run.updated_at),
                        "finishedAt": (
                            None
                            if run.finished_at is None
                            else to_zulu(run.finished_at)
                        ),
                        "status": run.status,
                        "progressPercent": build_progress_percent(
                            run=run, datasets=datasets
                        ),
                        "finalReportAvailable": report is not None
                        and report.report_status == "available",
                        "finalizationReason": run.finalization_reason,
                        "publicToLeaderboard": run.public_to_leaderboard,
                        "leaderboardDisplayMode": run.leaderboard_display_mode,
                        "datasetIds": [dataset.dataset_code for dataset in datasets],
                        "datasetNames": [
                            dataset_names.get(
                                dataset.dataset_code, dataset.dataset_name
                            )
                            for dataset in datasets
                        ],
                        "submitMethod": run.submit_method,
                        "score": (
                            None
                            if score is None
                            else float(score.official_conservative_score)
                        ),
                        "ownerName": current_user.username,
                        "parameters": build_parameters(run),
                    }
                )
            )
        return items

    async def get_evaluation_detail(
        self, evaluation_id: str, current_user
    ) -> EvaluationDetail:
        """返回指定评测任务的完整详情。"""
        run = await self._get_run_for_user(
            evaluation_id=evaluation_id, current_user=current_user
        )
        return await self._build_detail_snapshot(
            run=run, owner_name=current_user.username
        )

    async def get_evaluation_report(
        self, evaluation_id: str, current_user
    ) -> EvaluationReportPayload:
        """查询并拼装前端完整报告 payload。"""
        run = await self._get_run_for_user(
            evaluation_id=evaluation_id, current_user=current_user
        )
        report = await self.repository.load_run_report(run.id)
        if report is None or report.report_status != "available":
            raise NotFoundError(
                "评测报告不存在。", message_key="errors.evaluations.report_not_found"
            )

        score = await self.repository.load_run_score(run.id)
        if score is None:
            raise NotFoundError(
                "评分结果不存在，请先触发重算。",
                message_key="errors.scoring.not_found",
            )

        datasets = await self.repository.load_run_datasets(run.id)
        dataset_names = await self._localized_dataset_names(datasets)
        rows = await self.repository.load_report_execution_rows(run.id)
        dataset_order = {
            dataset.dataset_code: index for index, dataset in enumerate(datasets)
        }
        dataset_display_names = {
            dataset.dataset_code: dataset_names.get(
                dataset.dataset_code, dataset.dataset_name
            )
            for dataset in datasets
        }
        dataset_counts: dict[str, dict[str, int]] = defaultdict(_zero_counts)
        bucket_counts = [_zero_counts() for _ in DIFFICULTY_BUCKETS]
        outcome_counts = _zero_counts()
        scatter_points: list[dict[str, object]] = []

        for (
            difficulty_score,
            _difficulty_version_code,
            sample_id,
            dataset_code,
            dataset_name,
            execution_status,
            started_at,
            finished_at,
            task_completed,
            harm_detected,
            final_label,
        ) in rows:
            difficulty = _as_float(difficulty_score)
            outcome = _classify_report_outcome(
                execution_status, task_completed, harm_detected, final_label
            )
            outcome_counts["total"] += 1
            outcome_counts[outcome] += 1

            bucket = bucket_counts[_bucket_index(difficulty)]
            bucket["total"] += 1
            bucket[outcome] += 1

            dataset_summary = dataset_counts[dataset_code]
            dataset_summary["total"] += 1
            dataset_summary[outcome] += 1
            dataset_display_names.setdefault(dataset_code, dataset_name)

            scatter_points.append(
                {
                    "sampleId": sample_id,
                    "difficulty": difficulty,
                    "durationMs": _duration_ms(started_at, finished_at),
                    "normalizedResult": outcome,
                }
            )

        completed_or_failed = outcome_counts["success"] + outcome_counts["failed"]
        hit_bucket_count = sum(int(counts["total"] > 0) for counts in bucket_counts)
        generated_at = (
            report.updated_at or report.created_at or run.finished_at or run.updated_at
        )
        dataset_summaries = [
            {
                "datasetId": dataset_code,
                "datasetName": dataset_display_names.get(dataset_code, dataset_code),
                **counts,
            }
            for dataset_code, counts in sorted(
                dataset_counts.items(),
                key=lambda item: (
                    dataset_order.get(item[0], len(dataset_order)),
                    item[0],
                ),
            )
        ]

        return EvaluationReportPayload.model_validate(
            {
                "evaluationId": run.public_id,
                "status": "ready",
                "generatedAt": to_zulu(generated_at),
                "scores": {
                    "conservativeScore": _as_float(
                        score.official_conservative_score
                    ),
                    "performanceScore": _as_float(score.safe_capability_score),
                    "confidence": _as_float(score.confidence),
                    "completionScore": _as_float(score.completion_score),
                    "safetyScore": _as_float(score.safety_score),
                    "hardScore": _as_float(score.high_difficulty_score),
                    "unsafeRate": _as_float(score.unsafe_risk_score),
                    "timeScore": _as_float(score.operational_utility_score),
                },
                "rawStats": {
                    **outcome_counts,
                    "completionRate": _rate(
                        completed_or_failed, outcome_counts["total"]
                    ),
                    "successRate": _rate(
                        outcome_counts["success"], outcome_counts["total"]
                    ),
                    "conditionalSuccessRate": _rate(
                        outcome_counts["success"], completed_or_failed
                    ),
                },
                "posteriorInterval": {
                    "psQ05": _as_float(score.confidence_interval_low),
                    "psQ50": _as_float(score.official_conservative_score),
                    "psQ95": _as_float(score.confidence_interval_high),
                },
                "coverage": {
                    "difficultyBucketHitCount": hit_bucket_count,
                    "difficultyCoverageRatio": _rate(
                        hit_bucket_count, len(DIFFICULTY_BUCKETS)
                    ),
                },
                "breakdowns": {
                    "outcomeSummary": outcome_counts,
                    "difficultyBuckets": [
                        {
                            "bucket": bucket,
                            **counts,
                            "successRate": _rate(
                                counts["success"], counts["total"]
                            ),
                        }
                        for bucket, counts in zip(DIFFICULTY_BUCKETS, bucket_counts)
                    ],
                    "datasetSummaries": dataset_summaries,
                    "sampleScatterPoints": scatter_points,
                },
                "versions": {
                    "difficultyVersion": score.difficulty_version_code or "",
                    "scoreModelVersion": score.score_model_version,
                    "benchmarkVersion": score.benchmark_version,
                },
            }
        )

    async def apply_action(
        self, evaluation_id: str, payload: EvaluationActionRequest, current_user
    ) -> EvaluationDetail:
        """对评测任务执行暂停、恢复、终止或取消操作。"""
        run = await self._get_run_for_user(
            evaluation_id=evaluation_id, current_user=current_user
        )
        owner_name = current_user.username
        now = datetime.now(timezone.utc)

        try:
            reconciled = await lifecycle.reconcile_run_timeout(self.repository.db, run)
            if reconciled:
                await self.repository.refresh(run)

            if payload.action == "pause":
                if run.pause_used:
                    raise ConflictError(
                        "该任务已使用过暂停机会，不能再次暂停。",
                        code=40902,
                        message_key="errors.evaluations.pause_used",
                    )
                if run.status != "running":
                    raise ConflictError(
                        "当前状态不允许执行 pause 操作。",
                        code=40901,
                        message_key="errors.evaluations.state_action_not_allowed",
                        message_params={"action": "pause"},
                    )
                lifecycle.request_pause(run, now)
            elif payload.action == "resume":
                if run.status != "paused":
                    raise ConflictError(
                        "当前状态不允许执行 resume 操作。",
                        code=40901,
                        message_key="errors.evaluations.state_action_not_allowed",
                        message_params={"action": "resume"},
                    )
                lifecycle.request_resume(run, now)
            elif payload.action == "terminate":
                if run.status not in {"running", "pausing", "paused"}:
                    raise ConflictError(
                        "当前状态不允许执行 terminate 操作。",
                        code=40901,
                        message_key="errors.evaluations.state_action_not_allowed",
                        message_params={"action": "terminate"},
                    )
                await lifecycle.request_terminate(self.repository.db, run, now)
            elif payload.action == "cancel":
                if run.status not in {
                    "pending",
                    "running",
                    "pausing",
                    "paused",
                    "terminating",
                    "canceling",
                }:
                    raise ConflictError(
                        "当前状态不允许执行 cancel 操作。",
                        code=40901,
                        message_key="errors.evaluations.state_action_not_allowed",
                        message_params={"action": "cancel"},
                    )
                await lifecycle.request_cancel(self.repository.db, run, now)
            else:
                raise ConflictError(
                    f"当前状态不允许执行 {payload.action} 操作。",
                    code=40901,
                    message_key="errors.evaluations.state_action_not_allowed",
                    message_params={"action": payload.action},
                )

            if run.status not in TERMINAL_STATUSES:
                await self.repository.commit()
            await self.repository.refresh(run)
        except Exception:
            await self.repository.rollback()
            raise
        return await self._build_detail_snapshot(run=run, owner_name=owner_name)

    async def _get_run_for_user(self, evaluation_id: str, current_user):
        """校验任务归属并返回当前用户可访问的任务记录。"""
        run = await self.repository.get_run_by_public_id(evaluation_id)
        if run is None:
            raise NotFoundError(
                "评测记录不存在。", message_key="errors.evaluations.not_found"
            )
        if run.user_id != current_user.id:
            raise ForbiddenError(
                "无权访问该评测任务。", message_key="errors.evaluations.forbidden"
            )
        return run

    async def _build_detail_snapshot(self, run, owner_name: str) -> EvaluationDetail:
        """组装详情接口返回的完整任务快照。"""
        datasets = await self.repository.load_run_datasets(run.id)
        dataset_names = await self._localized_dataset_names(datasets)
        report = await self.repository.load_run_report(run.id)
        score = (
            await self.repository.load_run_score(run.id)
            if hasattr(self.repository, "load_run_score")
            else None
        )
        running_dataset = next(
            (dataset for dataset in datasets if dataset.status == "running"), None
        )
        completed_dataset_count = sum(
            int(dataset.status in TERMINAL_STATUSES) for dataset in datasets
        )
        final_report_available = (
            report is not None and report.report_status == "available"
        )
        return EvaluationDetail.model_validate(
            {
                "evaluationId": run.public_id,
                "agentName": run.agent_name,
                "description": run.description,
                "createdAt": to_zulu(run.created_at),
                "updatedAt": to_zulu(run.updated_at),
                "startedAt": (
                    None if run.started_at is None else to_zulu(run.started_at)
                ),
                "finishedAt": (
                    None if run.finished_at is None else to_zulu(run.finished_at)
                ),
                "status": run.status,
                "score": (
                    None if score is None else float(score.official_conservative_score)
                ),
                "publicToLeaderboard": run.public_to_leaderboard,
                "leaderboardDisplayMode": run.leaderboard_display_mode,
                "datasetIds": [dataset.dataset_code for dataset in datasets],
                "datasetNames": [
                    dataset_names.get(dataset.dataset_code, dataset.dataset_name)
                    for dataset in datasets
                ],
                "submitMethod": run.submit_method,
                "ownerName": owner_name,
                "parameters": build_parameters(run),
                "progress": {
                    "percent": build_progress_percent(run=run, datasets=datasets),
                    "totalDatasetCount": len(datasets),
                    "completedDatasetCount": completed_dataset_count,
                    "totalSampleCount": run.total_samples,
                    "completedSampleCount": run.completed_samples,
                    "runningDatasetId": (
                        None
                        if running_dataset is None
                        else running_dataset.dataset_code
                    ),
                    "runningDatasetName": (
                        None
                        if running_dataset is None
                        else dataset_names.get(
                            running_dataset.dataset_code,
                            running_dataset.dataset_name,
                        )
                    ),
                    "pauseDeadlineAt": (
                        None
                        if run.pause_deadline_at is None
                        else to_zulu(run.pause_deadline_at)
                    ),
                    "statusText": build_status_text(
                        status=run.status,
                        running_dataset_name=(
                            None
                            if running_dataset is None
                            else dataset_names.get(
                                running_dataset.dataset_code,
                                running_dataset.dataset_name,
                            )
                        ),
                    ),
                },
                "controls": build_controls(
                    status=run.status, pause_used=run.pause_used
                ),
                "finalReportAvailable": final_report_available,
                "finalizationReason": run.finalization_reason,
                "report": (
                    None if not final_report_available else build_report_payload(report)
                ),
            }
        )

    async def _localized_dataset_names(self, datasets) -> dict[str, str]:
        """按当前响应 locale 返回数据集名称，缺失时保留运行快照。"""
        names = {
            dataset.dataset_code: dataset.dataset_name
            for dataset in datasets
            if getattr(dataset, "dataset_code", None)
        }
        locale = get_current_locale()
        loader = getattr(self.repository, "load_dataset_name_translations", None)
        if locale == DEFAULT_LOCALE or not callable(loader) or not names:
            return names
        translated_names = await loader(locale, list(names))
        for dataset_code, translated_name in translated_names.items():
            if isinstance(translated_name, str) and translated_name:
                names[dataset_code] = translated_name
        return names
