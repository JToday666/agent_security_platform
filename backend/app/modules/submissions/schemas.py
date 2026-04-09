"""提交模块请求与响应模型。"""

from typing import Literal

from pydantic import Field

from app.shared.schemas import CamelModel


class ApiSubmitConfig(CamelModel):
    """API 提交方式的配置信息。"""

    base_url: str
    token: str | None = None


class DockerSubmitConfig(CamelModel):
    """Docker 提交方式的配置信息。"""

    image_uri: str
    username: str | None = None
    password: str | None = None


class SubmitParameters(CamelModel):
    """提交任务时的运行参数。"""

    difficulty: float
    timeout_minutes: int
    retry_enabled: bool = False


class AgentSubmissionRequest(CamelModel):
    """创建评测任务的请求体。"""

    agent_name: str = Field(max_length=100)
    description: str | None = None
    submit_method: Literal["api", "docker"]
    api: ApiSubmitConfig | None = None
    docker: DockerSubmitConfig | None = None
    parameters: SubmitParameters
    public_to_leaderboard: bool
    dataset_ids: list[str]
    request_id: str


class SubmitMetaRange(CamelModel):
    """提交页面滑块类配置项的范围描述。"""

    min: int | float
    max: int | float
    step: int | float
    default: int | float
    recommended_max: int | None = None


class SubmitMetaToggle(CamelModel):
    """提交页面开关类配置项的默认值。"""

    default: bool


class SubmitMetaResponse(CamelModel):
    """提交页面所需的元信息响应体。"""

    supported_methods: list[str]
    difficulty: SubmitMetaRange
    timeout_minutes: SubmitMetaRange
    retry_enabled: SubmitMetaToggle
    public_to_leaderboard: SubmitMetaToggle


class PrecheckResponse(CamelModel):
    """提交预检查接口响应体。"""

    ok: bool
    warnings: list[str]


class SubmitResponse(CamelModel):
    """提交成功后返回的任务摘要。"""

    evaluation_id: str
    status: str
    created_at: str
