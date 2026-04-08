from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import BackgroundTasks
from sqlalchemy import and_, case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.response import fail
from app.core.config import settings
from app.models.benchmark import BenchmarkSample, RiskSubtype
from app.models.benchmark_run import RunDataset, RunSample, SampleExecution, TestRun
from app.models.user import User
from app.schemas.agents import AgentSubmissionRequest
from app.services.runtime_rules import difficulty_bucket_bounds, is_valid_request_id
from app.services.secret_store import LocalSecretStore
from app.services.simulator import schedule_run_processing

SUPPORTED_METHODS = ["api", "docker"]
DIFFICULTY_META = {"min": 0, "max": 1, "step": 0.1, "default": 0.5}
TIMEOUT_META = {"min": 15, "max": 30, "step": 1, "default": 15, "recommendedMax": 20}

class SubmissionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_submit_meta(self) -> dict[str, object]:
        return {
            "supportedMethods": SUPPORTED_METHODS,
            "difficulty": DIFFICULTY_META,
            "timeoutMinutes": TIMEOUT_META,
            "retryEnabled": {"default": False},
            "publicToLeaderboard": {"default": True},
        }

    async def precheck(self, payload: AgentSubmissionRequest, current_user: User) -> dict[str, object]:
        warnings, _ = await self._validate_payload(payload)
        return {"ok": True, "warnings": warnings}

    async def submit(
        self,
        payload: AgentSubmissionRequest,
        current_user: User,
        background_tasks: BackgroundTasks | object | None = None,
    ) -> dict[str, object]:
        existing = (
            await self.db.execute(
                select(TestRun).where(
                    TestRun.user_id == current_user.id,
                    TestRun.request_id == payload.request_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return {
                "evaluationId": existing.public_id,
                "status": existing.status,
                "createdAt": to_zulu(existing.created_at),
            }

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
                "simulatedDatasetStepSeconds": settings.SIMULATED_DATASET_STEP_SECONDS,
            },
            total_samples=len(sample_rows),
            completed_samples=0,
            success_count=0,
            failed_count=0,
            created_at=now,
            updated_at=now,
        )
        self.db.add(run)
        await self.db.flush()

        matched_counts = selection["matched_counts"]
        run_datasets: list[RunDataset] = []
        for order_no, dataset_id in enumerate(selection["dataset_ids"], start=1):
            run_datasets.append(
                RunDataset(
                    run_id=run.id,
                    dataset_code=dataset_id,
                    dataset_name=selection["dataset_names"][dataset_id],
                    order_no=order_no,
                    status="pending",
                    total_samples=matched_counts[dataset_id],
                    completed_samples=0,
                )
            )
        self.db.add_all(run_datasets)

        run_samples: list[RunSample] = []
        global_order = 1
        for sample_row in sample_rows:
            run_samples.append(
                RunSample(
                    run_id=run.id,
                    sample_id_ref=sample_row.id,
                    order_no=global_order,
                )
            )
            global_order += 1
        self.db.add_all(run_samples)
        await self.db.flush()

        self.db.add_all(
            [
                SampleExecution(
                    run_id=run.id,
                    run_sample_id=run_sample.id,
                    sample_id_ref=run_sample.sample_id_ref,
                    status="pending",
                    retry_no=0,
                )
                for run_sample in run_samples
            ]
        )
        await self.db.commit()

        schedule_run_processing(background_tasks, run.id)
        return {
            "evaluationId": run.public_id,
            "status": run.status,
            "createdAt": to_zulu(run.created_at),
        }

    async def _validate_payload(self, payload: AgentSubmissionRequest) -> tuple[list[str], dict[str, object]]:
        agent_name = payload.agent_name.strip()
        if not agent_name:
            raise fail(400, 40002, "智能体名称不能为空。")
        if len(agent_name) > 100:
            raise fail(400, 40002, "智能体名称不能超过 100 个字符。")

        if payload.submit_method == "api":
            if payload.api is None or payload.docker is not None:
                raise fail(400, 40002, "提交方式参数不合法，请检查后重试。")
            if not payload.api.base_url.startswith(("http://", "https://")):
                raise fail(400, 40002, "API 地址不合法，请检查后重试。")
        elif payload.submit_method == "docker":
            if payload.docker is None or payload.api is not None:
                raise fail(400, 40002, "提交方式参数不合法，请检查后重试。")
            if not payload.docker.image_uri.strip():
                raise fail(400, 40002, "Docker 镜像地址不能为空。")
        else:
            raise fail(400, 40002, "提交方式参数不合法，请检查后重试。")

        if not (DIFFICULTY_META["min"] <= payload.parameters.difficulty <= DIFFICULTY_META["max"]):
            raise fail(400, 40002, "运行参数超出允许范围，请检查后重试。")
        if not (TIMEOUT_META["min"] <= payload.parameters.timeout_minutes <= TIMEOUT_META["max"]):
            raise fail(400, 40002, "运行参数超出允许范围，请检查后重试。")

        if not payload.dataset_ids:
            raise fail(400, 40002, "请至少选择一个评测项")

        ordered_dataset_ids = list(dict.fromkeys(payload.dataset_ids))
        if len(ordered_dataset_ids) != len(payload.dataset_ids):
            raise fail(400, 40002, "选择了重复或失效数据集。")

        if not is_valid_request_id(payload.request_id):
            raise fail(400, 40002, "requestId 格式不正确，请重试。")

        dataset_stmt = (
            select(RiskSubtype.code, RiskSubtype.name)
            .join(
                BenchmarkSample,
                and_(
                    BenchmarkSample.risk_subtype_id == RiskSubtype.id,
                    BenchmarkSample.is_active.is_(True),
                ),
            )
            .where(RiskSubtype.is_active.is_(True), RiskSubtype.code.in_(ordered_dataset_ids))
            .group_by(RiskSubtype.code, RiskSubtype.name)
        )
        dataset_rows = (await self.db.execute(dataset_stmt)).all()
        dataset_names = {code: name for code, name in dataset_rows}
        if len(dataset_names) != len(ordered_dataset_ids):
            raise fail(400, 40002, "选择了重复或失效数据集。")

        ordering = case({dataset_id: index for index, dataset_id in enumerate(ordered_dataset_ids)}, value=RiskSubtype.code)
        sample_stmt = (
            select(BenchmarkSample, RiskSubtype.code)
            .join(RiskSubtype, BenchmarkSample.risk_subtype_id == RiskSubtype.id)
            .where(
                BenchmarkSample.is_active.is_(True),
                RiskSubtype.code.in_(ordered_dataset_ids),
            )
            .order_by(ordering.asc(), BenchmarkSample.id.asc())
        )
        lower, upper, include_upper = difficulty_bucket_bounds(payload.parameters.difficulty)
        if include_upper:
            sample_stmt = sample_stmt.where(BenchmarkSample.difficulty_score >= lower, BenchmarkSample.difficulty_score <= upper)
        else:
            sample_stmt = sample_stmt.where(BenchmarkSample.difficulty_score >= lower, BenchmarkSample.difficulty_score < upper)

        sample_rows = (await self.db.execute(sample_stmt)).all()
        matched_counts: dict[str, int] = defaultdict(int)
        ordered_samples = []
        for sample, dataset_code in sample_rows:
            matched_counts[dataset_code] += 1
            ordered_samples.append(sample)

        warnings: list[str] = []
        if payload.public_to_leaderboard:
            warnings.append("本次结果将进入公开排行榜，请确认描述中不包含敏感信息。")
        if payload.parameters.timeout_minutes > TIMEOUT_META["recommendedMax"]:
            warnings.append("当前超时时间高于建议值 20，评测排队与执行耗时可能更长。")
        if not ordered_samples:
            raise fail(400, 40002, "当前条件下没有可执行样本，请调整评测项或难度。")

        return warnings, {
            "dataset_ids": ordered_dataset_ids,
            "dataset_names": dataset_names,
            "sample_rows": ordered_samples,
            "matched_counts": {dataset_id: matched_counts.get(dataset_id, 0) for dataset_id in ordered_dataset_ids},
        }

    def _store_credentials(self, payload: AgentSubmissionRequest) -> str | None:
        store = LocalSecretStore(settings.CREDENTIAL_STORAGE_DIR, settings.SECRET_KEY)
        if payload.submit_method == "api" and payload.api is not None and payload.api.token:
            return store.store(
                {
                    "submitMethod": payload.submit_method,
                    "baseUrl": payload.api.base_url,
                    "token": payload.api.token,
                }
            )
        if payload.submit_method == "docker" and payload.docker is not None and (payload.docker.username or payload.docker.password):
            return store.store(
                {
                    "submitMethod": payload.submit_method,
                    "imageUri": payload.docker.image_uri,
                    "username": payload.docker.username,
                    "password": payload.docker.password,
                }
            )
        return None


def to_zulu(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def generate_public_id() -> str:
    return f"eval_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
