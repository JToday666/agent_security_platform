"""评分模块 API 模型。"""

from app.modules.scoring.engine import (
    DEFAULT_BENCHMARK_VERSION,
    DEFAULT_SCORE_MODEL_VERSION,
)
from app.platform.schemas import CamelModel


class ScoreRecalculateRequest(CamelModel):
    """重算评测评分请求。"""

    score_model_version: str = DEFAULT_SCORE_MODEL_VERSION
    benchmark_version: str = DEFAULT_BENCHMARK_VERSION


class EvaluationScoreResponse(CamelModel):
    """评测评分响应。"""

    evaluation_id: str
    official_conservative_score: float
    safe_capability_score: float
    completion_score: float
    safety_score: float
    unsafe_risk_score: float
    high_difficulty_score: float
    operational_utility_score: float
    confidence: float
    confidence_interval90: list[float]
    verification_tier: str
    safety_certification: str
