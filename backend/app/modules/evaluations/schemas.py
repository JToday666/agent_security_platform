"""评测任务模块请求与响应模型。"""

from typing import Literal

from app.shared.schemas import CamelModel


class EvaluationParameters(CamelModel):
    """评测任务运行参数。"""

    difficulty: float
    timeout_minutes: int
    retry_enabled: bool


class EvaluationListItem(CamelModel):
    """评测任务列表中的单项摘要。"""

    evaluation_id: str
    agent_name: str
    description: str | None = None
    created_at: str
    updated_at: str
    status: str
    progress_percent: int
    final_report_available: bool
    finalization_reason: str | None = None
    public_to_leaderboard: bool
    dataset_ids: list[str]
    dataset_names: list[str]
    submit_method: str
    score: float | None = None
    owner_name: str
    parameters: EvaluationParameters


class EvaluationProgress(CamelModel):
    """评测任务进度信息。"""

    percent: int
    total_dataset_count: int
    completed_dataset_count: int
    running_dataset_id: str | None = None
    running_dataset_name: str | None = None
    pause_deadline_at: str | None = None
    status_text: str


class EvaluationControls(CamelModel):
    """当前评测任务允许执行的操作集合。"""

    can_pause: bool
    can_resume: bool
    can_terminate: bool
    can_cancel: bool
    pause_used: bool


class EvaluationReportSummary(CamelModel):
    """评测报告中的摘要统计。"""

    total_samples: int
    completed_samples: int
    task_completed_count: int
    harm_detected_count: int
    failed_count: int
    by_risk_category: list[dict[str, object]]
    by_risk_level: list[dict[str, object]]
    by_attack_level: list[dict[str, object]]


class EvaluationReport(CamelModel):
    """评测报告响应体。"""

    report_status: str
    summary: EvaluationReportSummary
    report_uri: str | None = None


class EvaluationDetail(CamelModel):
    """评测任务详情响应体。"""

    evaluation_id: str
    agent_name: str
    description: str | None = None
    created_at: str
    updated_at: str
    status: str
    score: float | None = None
    public_to_leaderboard: bool
    dataset_ids: list[str]
    dataset_names: list[str]
    submit_method: str
    owner_name: str
    parameters: EvaluationParameters
    progress: EvaluationProgress
    controls: EvaluationControls
    final_report_available: bool
    finalization_reason: str | None = None
    report: EvaluationReport | None = None


class EvaluationActionRequest(CamelModel):
    """评测任务动作请求体。"""

    action: Literal["pause", "resume", "terminate", "cancel"]


class EvaluationActionResult(CamelModel):
    """评测任务动作处理结果。"""

    evaluation_id: str
    status: str
    controls: EvaluationControls
