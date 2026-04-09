from typing import Literal

from pydantic import Field

from app.shared.schemas import CamelModel


class ApiSubmitConfig(CamelModel):
    base_url: str
    token: str | None = None


class DockerSubmitConfig(CamelModel):
    image_uri: str
    username: str | None = None
    password: str | None = None


class SubmitParameters(CamelModel):
    difficulty: float
    timeout_minutes: int
    retry_enabled: bool = False


class AgentSubmissionRequest(CamelModel):
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
    min: int | float
    max: int | float
    step: int | float
    default: int | float
    recommended_max: int | None = None


class SubmitMetaToggle(CamelModel):
    default: bool


class SubmitMetaResponse(CamelModel):
    supported_methods: list[str]
    difficulty: SubmitMetaRange
    timeout_minutes: SubmitMetaRange
    retry_enabled: SubmitMetaToggle
    public_to_leaderboard: SubmitMetaToggle


class PrecheckResponse(CamelModel):
    ok: bool
    warnings: list[str]


class SubmitResponse(CamelModel):
    evaluation_id: str
    status: str
    created_at: str
