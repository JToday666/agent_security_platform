"""评测任务模块服务，负责列表、详情与任务动作编排。"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.models.benchmark_run import TestRun
from app.modules.evaluations import lifecycle
from app.modules.evaluations.repository import EvaluationRepository
from app.modules.evaluations.schemas import (
    EvaluationActionRequest,
    EvaluationCreateRequest,
    EvaluationCreateResponse,
    EvaluationDetail,
    EvaluationListItem,
    EvaluationSubmitMeta,
    EvaluationValidateResponse,
)
from app.modules.evaluations.state_rules import TERMINAL_STATUSES, build_controls
from app.shared.errors import ConflictError, ForbiddenError, NotFoundError, ValidationDomainError
from app.shared.runtime_rules import difficulty_bucket_bounds, is_valid_request_id


DIFFICULTY_META = {"min": 0, "max": 1, "step": 0.1, "default": 0.5}
TIMEOUT_META = {"min": 15, "max": 30, "step": 1, "default": 15}
MAX_STEPS_META = {"min": 1, "max": 100, "default": 30}


def to_zulu(value: datetime) -> str:
    """将时间转换为接口使用的 UTC 字符串。"""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def invalid_evaluation(message: str) -> ValidationDomainError:
    """构造评测提交参数错误。"""
    return ValidationDomainError(message, http_status=400, code=40002)


def generate_public_id() -> str:
    """生成对外评测任务编号。"""
    return f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"


def request_fingerprint(payload: EvaluationCreateRequest) -> str:
    """对提交请求体做稳定哈希，供 requestId 幂等校验。"""
    encoded = json.dumps(payload.model_dump(by_alias=True), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def agent_runtime_snapshot(agent) -> dict[str, object]:
    """冻结 Agent 运行配置，供 worker 后续调用。"""
    return {
        "agentId": agent.public_id,
        "templateId": agent.template_id,
        "name": agent.name,
        "description": agent.description,
        "invokeMode": agent.invoke_mode,
        "connection": agent.connection,
        "auth": {"type": agent.auth_type, **agent.auth_public_config, "credentialRef": agent.credential_ref},
        "platformInputMapping": agent.platform_input_mapping,
        "taskRenderMode": agent.task_render_mode,
        "customRequestBody": agent.custom_request_body,
        "requestOptions": agent.request_options,
        "platformOutputMapping": agent.platform_output_mapping,
        "terminalStatuses": agent.terminal_statuses,
        "successStatuses": agent.success_statuses,
    }


def build_parameters(run) -> dict[str, object]:
    """整理评测任务保存的运行参数。"""
    return run.execution_config.get(
        "parameters",
        {"difficulty": 0.5, "timeoutMinutes": 15, "retryEnabled": False},
    )


def build_progress_percent(run, datasets: list) -> int:
    """计算评测任务当前进度百分比。"""
    if run.total_samples > 0:
        return max(0, min(100, round((run.completed_samples / run.total_samples) * 100)))
    if not datasets:
        return 0
    completed = sum(int(dataset.status in TERMINAL_STATUSES) for dataset in datasets)
    return max(0, min(100, round((completed / len(datasets)) * 100)))


def build_status_text(status: str, running_dataset_name: str | None) -> str:
    """生成面向前端展示的状态文案。"""
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
    """整理评测报告响应体。"""
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
            }
        )

    async def validate_submission(self, payload: EvaluationCreateRequest, current_user) -> EvaluationValidateResponse:
        """校验评测提交请求。"""
        warnings, _selection, _agent = await self._validate_submission_payload(payload, current_user)
        return EvaluationValidateResponse(ok=True, warnings=warnings)

    async def create_evaluation(self, payload: EvaluationCreateRequest, current_user) -> EvaluationCreateResponse:
        """创建评测任务并冻结 Agent 配置。"""
        fingerprint = request_fingerprint(payload)
        existing = await self.repository.get_existing_run(current_user.id, payload.request_id)
        if existing is not None:
            if existing.sample_query_snapshot.get("requestBodyHash") != fingerprint:
                raise ConflictError("requestId 已被不同请求体使用。", code=40900)
            return EvaluationCreateResponse(
                evaluation_id=existing.public_id,
                submit_method=existing.submit_method,
                agent_id=str(existing.execution_config.get("agentId") or payload.agent_id),
                status=existing.status,
                created_at=to_zulu(existing.created_at),
            )

        warnings, selection, agent = await self._validate_submission_payload(payload, current_user)
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
            public_to_leaderboard=payload.public_to_leaderboard,
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
            existing = await self.repository.get_existing_run(current_user.id, payload.request_id)
            if existing is not None and existing.sample_query_snapshot.get("requestBodyHash") == fingerprint:
                return EvaluationCreateResponse(
                    evaluation_id=existing.public_id,
                    submit_method=existing.submit_method,
                    agent_id=str(existing.execution_config.get("agentId") or payload.agent_id),
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
        datasets_by_run, reports_by_run = await self.repository.load_related_for_runs([run.id for run in runs])
        scores_by_run = {}
        if hasattr(self.repository, "load_scores_for_runs"):
            scores_by_run = await self.repository.load_scores_for_runs([run.id for run in runs])
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
                        "status": run.status,
                        "progressPercent": build_progress_percent(run=run, datasets=datasets),
                        "finalReportAvailable": report is not None and report.report_status == "available",
                        "finalizationReason": run.finalization_reason,
                        "publicToLeaderboard": run.public_to_leaderboard,
                        "datasetIds": [dataset.dataset_code for dataset in datasets],
                        "datasetNames": [dataset.dataset_name for dataset in datasets],
                        "submitMethod": run.submit_method,
                        "score": None if score is None else float(score.official_conservative_score),
                        "ownerName": current_user.username,
                        "parameters": build_parameters(run),
                    }
                )
            )
        return items

    async def _validate_submission_payload(self, payload: EvaluationCreateRequest, current_user):
        """校验新评测提交请求并返回样本选择与 Agent。"""
        if payload.submit_method != "api":
            raise invalid_evaluation("提交方式参数不合法，请检查后重试。")
        if not is_valid_request_id(payload.request_id):
            raise invalid_evaluation("requestId 格式不正确，请重试。")
        if not (DIFFICULTY_META["min"] <= payload.parameters.difficulty <= DIFFICULTY_META["max"]):
            raise invalid_evaluation("运行参数超出允许范围，请检查后重试。")
        if not (TIMEOUT_META["min"] <= payload.parameters.timeout_minutes <= TIMEOUT_META["max"]):
            raise invalid_evaluation("运行参数超出允许范围，请检查后重试。")
        if not (MAX_STEPS_META["min"] <= payload.parameters.max_steps <= MAX_STEPS_META["max"]):
            raise invalid_evaluation("运行参数超出允许范围，请检查后重试。")
        if not payload.dataset_ids:
            raise invalid_evaluation("请至少选择一个评测项")

        agent = await self.repository.get_agent_by_public_id(payload.agent_id)
        if agent is None:
            raise NotFoundError("Agent 不存在。")
        if agent.user_id != current_user.id:
            raise ForbiddenError("无权访问该 Agent。")
        if agent.status != "active":
            raise ConflictError(
                f"Agent 当前状态为 {agent.status}，不能提交评测。",
                code=40901,
                data={"agentId": agent.public_id, "status": agent.status},
            )

        ordered_dataset_ids = list(dict.fromkeys(payload.dataset_ids))
        if len(ordered_dataset_ids) != len(payload.dataset_ids):
            raise invalid_evaluation("选择了重复或失效数据集。")

        selection = await self.repository.resolve_dataset_selection(ordered_dataset_ids, payload.parameters.difficulty)
        if len(selection["dataset_names"]) != len(ordered_dataset_ids):
            raise invalid_evaluation("选择了重复或失效数据集。")
        if not selection["sample_rows"]:
            raise invalid_evaluation("当前条件下没有可执行样本，请调整评测项或难度。")

        difficulty_bucket_bounds(payload.parameters.difficulty)
        warnings: list[dict[str, str]] = []
        if payload.public_to_leaderboard:
            warnings.append({"code": "PUBLIC_LEADERBOARD", "message": "本次结果将进入公开排行榜，请确认描述中不包含敏感信息。"})
        return warnings, {
            "dataset_ids": ordered_dataset_ids,
            "dataset_names": selection["dataset_names"],
            "sample_rows": selection["sample_rows"],
            "matched_counts": selection["matched_counts"],
        }, agent

    async def get_evaluation_detail(self, evaluation_id: str, current_user) -> EvaluationDetail:
        """返回指定评测任务的完整详情。"""
        run = await self._get_run_for_user(evaluation_id=evaluation_id, current_user=current_user)
        return await self._build_detail_snapshot(run=run, owner_name=current_user.username)

    async def apply_action(self, evaluation_id: str, payload: EvaluationActionRequest, current_user) -> EvaluationDetail:
        """对评测任务执行暂停、恢复、终止或取消操作。"""
        run = await self._get_run_for_user(evaluation_id=evaluation_id, current_user=current_user)
        owner_name = current_user.username
        now = datetime.now(timezone.utc)

        try:
            reconciled = await lifecycle.reconcile_run_timeout(self.repository.db, run)
            if reconciled:
                await self.repository.refresh(run)

            if payload.action == "pause":
                if run.pause_used:
                    raise ConflictError("该任务已使用过暂停机会，不能再次暂停。", code=40902)
                if run.status != "running":
                    raise ConflictError("当前状态不允许执行 pause 操作。", code=40901)
                lifecycle.request_pause(run, now)
            elif payload.action == "resume":
                if run.status != "paused":
                    raise ConflictError("当前状态不允许执行 resume 操作。", code=40901)
                lifecycle.request_resume(run, now)
            elif payload.action == "terminate":
                if run.status not in {"running", "pausing", "paused"}:
                    raise ConflictError("当前状态不允许执行 terminate 操作。", code=40901)
                await lifecycle.request_terminate(self.repository.db, run, now)
            elif payload.action == "cancel":
                if run.status not in {"pending", "running", "pausing", "paused", "terminating", "canceling"}:
                    raise ConflictError("当前状态不允许执行 cancel 操作。", code=40901)
                await lifecycle.request_cancel(self.repository.db, run, now)
            else:
                raise ConflictError(f"当前状态不允许执行 {payload.action} 操作。", code=40901)

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
            raise NotFoundError("评测记录不存在。")
        if run.user_id != current_user.id:
            raise ForbiddenError("无权访问该评测任务。")
        return run

    async def _build_detail_snapshot(self, run, owner_name: str) -> EvaluationDetail:
        """组装详情接口返回的完整任务快照。"""
        datasets = await self.repository.load_run_datasets(run.id)
        report = await self.repository.load_run_report(run.id)
        score = await self.repository.load_run_score(run.id) if hasattr(self.repository, "load_run_score") else None
        running_dataset = next((dataset for dataset in datasets if dataset.status == "running"), None)
        completed_dataset_count = sum(int(dataset.status in TERMINAL_STATUSES) for dataset in datasets)
        final_report_available = report is not None and report.report_status == "available"
        return EvaluationDetail.model_validate(
            {
                "evaluationId": run.public_id,
                "agentName": run.agent_name,
                "description": run.description,
                "createdAt": to_zulu(run.created_at),
                "updatedAt": to_zulu(run.updated_at),
                "status": run.status,
                "score": None if score is None else float(score.official_conservative_score),
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
        )
