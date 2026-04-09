from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.benchmark_run import TestRun
from app.modules.submissions.repository import SubmissionRepository
from app.modules.submissions.schemas import (
    AgentSubmissionRequest,
    PrecheckResponse,
    SubmitMetaResponse,
    SubmitResponse,
)
from app.shared.config import settings
from app.shared.credentials import CredentialStore, FileCredentialStore
from app.shared.errors import ValidationDomainError
from app.shared.runtime_rules import difficulty_bucket_bounds, is_valid_request_id

SUPPORTED_METHODS = ["api", "docker"]
DIFFICULTY_META = {"min": 0, "max": 1, "step": 0.1, "default": 0.5}
TIMEOUT_META = {"min": 15, "max": 30, "step": 1, "default": 15, "recommendedMax": 20}


def invalid_submission(message: str) -> ValidationDomainError:
    return ValidationDomainError(message, http_status=400, code=40002)


def to_zulu(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def generate_public_id() -> str:
    return f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"


class SubmissionService:
    def __init__(self, repository: SubmissionRepository, credential_store: CredentialStore | None = None) -> None:
        self.repository = repository
        self.credential_store = credential_store or FileCredentialStore(settings.credential_storage_dir, settings.SECRET_KEY)

    async def get_submit_meta(self) -> SubmitMetaResponse:
        return SubmitMetaResponse.model_validate(
            {
                "supportedMethods": SUPPORTED_METHODS,
                "difficulty": DIFFICULTY_META,
                "timeoutMinutes": TIMEOUT_META,
                "retryEnabled": {"default": False},
                "publicToLeaderboard": {"default": True},
            }
        )

    async def precheck(self, payload: AgentSubmissionRequest, current_user) -> PrecheckResponse:
        warnings, _ = await self._validate_payload(payload)
        return PrecheckResponse(ok=True, warnings=warnings)

    async def submit(self, payload: AgentSubmissionRequest, current_user) -> SubmitResponse:
        existing = await self.repository.get_existing_run(current_user.id, payload.request_id)
        if existing is not None:
            return SubmitResponse(
                evaluation_id=existing.public_id,
                status=existing.status,
                created_at=to_zulu(existing.created_at),
            )

        warnings, selection = await self._validate_payload(payload)
        sample_rows = selection["sample_rows"]
        credential_ref = self._store_credentials(payload)
        public_id = generate_public_id()
        now = datetime.now(timezone.utc)
        parameter_snapshot = {
            "difficulty": payload.parameters.difficulty,
            "timeoutMinutes": payload.parameters.timeout_minutes,
            "retryEnabled": payload.parameters.retry_enabled,
        }
        run = TestRun(
            user_id=current_user.id,
            public_id=public_id,
            agent_name=payload.agent_name.strip(),
            description=(payload.description or "").strip() or None,
            submit_method=payload.submit_method,
            public_to_leaderboard=payload.public_to_leaderboard,
            request_id=payload.request_id,
            agent_base_url=payload.api.base_url if payload.submit_method == "api" else payload.docker.image_uri,
            credential_ref=credential_ref,
            status="pending",
            sample_query_snapshot={
                "datasetIds": selection["dataset_ids"],
                "difficulty": payload.parameters.difficulty,
                "matchedSampleCount": len(sample_rows),
                "matchedDatasetCount": len(selection["dataset_ids"]),
                "warnings": warnings,
            },
            execution_config={
                "parameters": parameter_snapshot,
                "agentTarget": {
                    "baseUrl": payload.api.base_url if payload.api is not None else None,
                    "imageUri": payload.docker.image_uri if payload.docker is not None else None,
                },
            },
            total_samples=len(sample_rows),
            completed_samples=0,
            success_count=0,
            failed_count=0,
            created_at=now,
            updated_at=now,
            claimed_by=None,
            claimed_at=None,
            claim_heartbeat_at=None,
        )
        run = await self.repository.create_run_graph(
            run=run,
            dataset_ids=selection["dataset_ids"],
            dataset_names=selection["dataset_names"],
            matched_counts=selection["matched_counts"],
            sample_rows=sample_rows,
        )
        return SubmitResponse(
            evaluation_id=run.public_id,
            status=run.status,
            created_at=to_zulu(run.created_at),
        )

    async def _validate_payload(self, payload: AgentSubmissionRequest) -> tuple[list[str], dict[str, object]]:
        agent_name = payload.agent_name.strip()
        if not agent_name:
            raise invalid_submission("智能体名称不能为空。")
        if len(agent_name) > 100:
            raise invalid_submission("智能体名称不能超过 100 个字符。")

        if payload.submit_method == "api":
            if payload.api is None or payload.docker is not None:
                raise invalid_submission("提交方式参数不合法，请检查后重试。")
            if not payload.api.base_url.startswith(("http://", "https://")):
                raise invalid_submission("API 地址不合法，请检查后重试。")
        elif payload.submit_method == "docker":
            if payload.docker is None or payload.api is not None:
                raise invalid_submission("提交方式参数不合法，请检查后重试。")
            if not payload.docker.image_uri.strip():
                raise invalid_submission("Docker 镜像地址不能为空。")
        else:
            raise invalid_submission("提交方式参数不合法，请检查后重试。")

        if not (DIFFICULTY_META["min"] <= payload.parameters.difficulty <= DIFFICULTY_META["max"]):
            raise invalid_submission("运行参数超出允许范围，请检查后重试。")
        if not (TIMEOUT_META["min"] <= payload.parameters.timeout_minutes <= TIMEOUT_META["max"]):
            raise invalid_submission("运行参数超出允许范围，请检查后重试。")

        if not payload.dataset_ids:
            raise invalid_submission("请至少选择一个评测项")

        ordered_dataset_ids = list(dict.fromkeys(payload.dataset_ids))
        if len(ordered_dataset_ids) != len(payload.dataset_ids):
            raise invalid_submission("选择了重复或失效数据集。")

        if not is_valid_request_id(payload.request_id):
            raise invalid_submission("requestId 格式不正确，请重试。")

        selection = await self.repository.resolve_dataset_selection(ordered_dataset_ids, payload.parameters.difficulty)
        dataset_names = selection["dataset_names"]
        if len(dataset_names) != len(ordered_dataset_ids):
            raise invalid_submission("选择了重复或失效数据集。")

        sample_rows = selection["sample_rows"]
        warnings: list[str] = []
        if payload.public_to_leaderboard:
            warnings.append("本次结果将进入公开排行榜，请确认描述中不包含敏感信息。")
        if payload.parameters.timeout_minutes > TIMEOUT_META["recommendedMax"]:
            warnings.append("当前超时时间高于建议值 20，评测排队与执行耗时可能更长。")
        if not sample_rows:
            raise invalid_submission("当前条件下没有可执行样本，请调整评测项或难度。")

        difficulty_bucket_bounds(payload.parameters.difficulty)
        return warnings, {
            "dataset_ids": ordered_dataset_ids,
            "dataset_names": dataset_names,
            "sample_rows": sample_rows,
            "matched_counts": selection["matched_counts"],
        }

    def _store_credentials(self, payload: AgentSubmissionRequest) -> str | None:
        if payload.submit_method == "api" and payload.api is not None and payload.api.token:
            return self.credential_store.store(
                {
                    "submitMethod": payload.submit_method,
                    "baseUrl": payload.api.base_url,
                    "token": payload.api.token,
                }
            )
        if payload.submit_method == "docker" and payload.docker is not None and (payload.docker.username or payload.docker.password):
            return self.credential_store.store(
                {
                    "submitMethod": payload.submit_method,
                    "imageUri": payload.docker.image_uri,
                    "username": payload.docker.username,
                    "password": payload.docker.password,
                }
            )
        return None
