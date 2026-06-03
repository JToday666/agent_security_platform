"""Submission validation for evaluation creation."""

from __future__ import annotations

from app.modules.evaluations.domain.constants import (
    DIFFICULTY_META,
    MAX_STEPS_META,
    TIMEOUT_META,
)
from app.modules.evaluations.schemas import EvaluationCreateRequest
from app.platform.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationDomainError,
)
from app.platform.i18n import translate
from app.platform.runtime_rules import difficulty_bucket_bounds, is_valid_request_id


def invalid_evaluation(message: str, *, message_key: str) -> ValidationDomainError:
    """Build evaluation submission validation errors."""
    return ValidationDomainError(
        message, http_status=400, code=40002, message_key=message_key
    )


async def validate_submission_payload(
    repository, payload: EvaluationCreateRequest, current_user
):
    """Validate a new evaluation request and resolve its selected samples and Agent."""
    if payload.submit_method != "api":
        raise invalid_evaluation(
            "提交方式参数不合法，请检查后重试。",
            message_key="errors.evaluations.submit_method_invalid",
        )
    if not is_valid_request_id(payload.request_id):
        raise invalid_evaluation(
            "requestId 格式不正确，请重试。",
            message_key="errors.evaluations.request_id_invalid",
        )
    if not (
        DIFFICULTY_META["min"]
        <= payload.parameters.difficulty
        <= DIFFICULTY_META["max"]
    ):
        raise invalid_evaluation(
            "运行参数超出允许范围，请检查后重试。",
            message_key="errors.evaluations.parameters_out_of_range",
        )
    if not (
        TIMEOUT_META["min"] <= payload.parameters.timeout_minutes <= TIMEOUT_META["max"]
    ):
        raise invalid_evaluation(
            "运行参数超出允许范围，请检查后重试。",
            message_key="errors.evaluations.parameters_out_of_range",
        )
    if not (
        MAX_STEPS_META["min"] <= payload.parameters.max_steps <= MAX_STEPS_META["max"]
    ):
        raise invalid_evaluation(
            "运行参数超出允许范围，请检查后重试。",
            message_key="errors.evaluations.parameters_out_of_range",
        )
    if not payload.attack_scenario_id:
        raise invalid_evaluation(
            "请选择攻击场景。", message_key="errors.evaluations.attack_scenario_required"
        )
    if not payload.evaluation_item_ids:
        raise invalid_evaluation(
            "请至少选择一个评测项", message_key="errors.evaluations.dataset_required"
        )

    agent = await repository.get_agent_by_public_id(payload.agent_id)
    if agent is None:
        raise NotFoundError(
            "Agent 不存在。", message_key="errors.evaluations.agent_not_found"
        )
    if agent.user_id != current_user.id:
        raise ForbiddenError(
            "无权访问该 Agent。", message_key="errors.evaluations.agent_forbidden"
        )
    if agent.status != "active":
        raise ConflictError(
            f"Agent 当前状态为 {agent.status}，不能提交评测。",
            code=40901,
            data={"agentId": agent.public_id, "status": agent.status},
            message_key="errors.evaluations.agent_status_invalid",
            message_params={"status": agent.status},
        )

    ordered_evaluation_item_ids = list(dict.fromkeys(payload.evaluation_item_ids))
    if len(ordered_evaluation_item_ids) != len(payload.evaluation_item_ids):
        raise invalid_evaluation(
            "选择了重复或失效评测项。", message_key="errors.evaluations.dataset_invalid"
        )

    selection = await repository.resolve_dataset_selection(
        payload.attack_scenario_id,
        ordered_evaluation_item_ids,
        payload.parameters.difficulty,
    )
    if len(selection["evaluation_item_names"]) != len(ordered_evaluation_item_ids):
        raise invalid_evaluation(
            "所选评测项不属于当前攻击场景或已失效。",
            message_key="errors.evaluations.attack_scenario_mismatch",
        )
    if not selection["sample_rows"]:
        raise invalid_evaluation(
            "当前条件下没有可执行样本，请调整评测项或难度。",
            message_key="errors.evaluations.no_samples",
        )

    difficulty_bucket_bounds(payload.parameters.difficulty)
    warnings: list[dict[str, str]] = []
    if payload.public_to_leaderboard:
        warnings.append(
            {
                "code": "PUBLIC_LEADERBOARD",
                "message": translate("errors.evaluations.public_leaderboard_warning"),
            }
        )
    return (
        warnings,
        {
            "attack_scenario_id": payload.attack_scenario_id,
            "attack_scenario_name": selection.get("attack_scenario_name"),
            "evaluation_item_ids": ordered_evaluation_item_ids,
            "evaluation_item_names": selection["evaluation_item_names"],
            "sample_rows": selection["sample_rows"],
            "matched_counts": selection["matched_counts"],
        },
        agent,
    )
