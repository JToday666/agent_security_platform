"""动态难度 API 模型。"""

from app.platform.schemas import CamelModel


class DifficultyRecalculateRequest(CamelModel):
    """重算难度版本请求。"""

    base_version_code: str = "legacy_current"
    new_version_code: str
    stats_cutoff_at: str | None = None


class DifficultyVersionResult(CamelModel):
    """难度版本操作响应。"""

    version_code: str
    status: str
    item_count: int


class DifficultyPublishResult(CamelModel):
    """难度版本发布响应。"""

    version_code: str
    status: str
    published_item_count: int
