"""Submission validation for evaluation creation."""

from __future__ import annotations

from app.modules.evaluations.domain.constants import DIFFICULTY_META, MAX_STEPS_META, TIMEOUT_META
from app.modules.evaluations.schemas import EvaluationCreateRequest
from app.platform.errors import ConflictError, ForbiddenError, NotFoundError, ValidationDomainError
from app.platform.runtime_rules import difficulty_bucket_bounds, is_valid_request_id


def invalid_evaluation(message: str) -> ValidationDomainError:
    """Build evaluation submission validation errors."""
    return ValidationDomainError(message, http_status=400, code=40002)


async def validate_submission_payload(repository, payload: EvaluationCreateRequest, current_user):
    """Validate a new evaluation request and resolve its selected samples and Agent."""
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

    agent = await repository.get_agent_by_public_id(payload.agent_id)
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

    selection = await repository.resolve_dataset_selection(ordered_dataset_ids, payload.parameters.difficulty)
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

