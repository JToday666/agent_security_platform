"""排行榜 API 模型。"""

from app.platform.schemas import CamelModel


class LeaderboardSnapshotCreateRequest(CamelModel):
    """生成排行榜快照请求。"""

    score_model_version: str = "score_v1_5"
    benchmark_version: str = "bm_v1"


class LeaderboardEntryItem(CamelModel):
    """排行榜条目。"""

    rank_no: int
    agent_id: str
    agent_name: str
    evaluation_id: str
    official_conservative_score: float
    safe_capability_score: float
    high_difficulty_score: float
    unsafe_risk_score: float
    confidence: float
    verification_tier: str
    safety_certification: str
    total_samples: int


class LeaderboardSnapshotResponse(CamelModel):
    """排行榜快照响应。"""

    snapshot_code: str
    entry_count: int
    entries: list[LeaderboardEntryItem]
