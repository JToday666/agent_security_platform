from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, select

from app.models.benchmark import (
    AttackDeliveryType,
    BenchmarkSample,
    DatasetSource,
    RiskCategory,
    RiskSubtype,
    RiskSubtypeDisplayMeta,
)
from app.models.benchmark_run import (
    ExecutionArtifact,
    ExecutionSummary,
    OracleResult,
    RunDataset,
    RunReport,
    RunSample,
    SampleDifficultyStat,
    SampleExecution,
    TestRun,
)
from app.models.scoring import (
    DifficultyVersion,
    DifficultyVersionItem,
    EvaluationScore,
    LeaderboardEntry,
    LeaderboardSnapshot,
)
from app.models.agent import Agent
from app.models.user import User
from app.shared.security import create_access_token, hash_password


@dataclass(slots=True)
class ApiDbHelper:
    """为真实数据库 API 烟测提供种子数据与清理能力。"""

    session_factory: object
    prefix: str
    created_avatar_paths: list[Path] = field(default_factory=list)

    def session(self):
        return self.session_factory()

    def seed_user(self, *, username: str, email: str) -> tuple[int, str]:
        with self.session() as session:
            user = User(username=username, email=email, hashed_password=hash_password("secret123"))
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.id, create_access_token(user.id)

    def seed_dataset(self) -> str:
        dataset_code = f"{self.prefix}_dataset"
        with self.session() as session:
            category = RiskCategory(
                code=f"{self.prefix}_category",
                name=f"{self.prefix} 大类",
                meaning="烟测大类",
                description="真实数据库烟测数据",
                sort_order=1,
                is_active=True,
            )
            source = DatasetSource(code=f"{self.prefix}_source", name=f"{self.prefix} source", is_active=True)
            delivery = AttackDeliveryType(code=f"{self.prefix}_delivery", name=f"{self.prefix} delivery", is_active=True)
            session.add_all([category, source, delivery])
            session.flush()

            subtype = RiskSubtype(
                category_id=category.id,
                code=dataset_code,
                name=f"{self.prefix} 数据集",
                sort_order=1,
                is_active=True,
            )
            session.add(subtype)
            session.flush()

            session.add(
                RiskSubtypeDisplayMeta(
                    subtype_id=subtype.id,
                    short_description="短描述",
                    full_description="完整描述",
                    highlights=["亮点一"],
                    scenarios=["场景一"],
                    resources=[{"label": "文档", "url": "https://example.com/docs", "type": "docs"}],
                    media=[
                        {
                            "mediaId": "demo",
                            "type": "image",
                            "title": "示意图",
                            "description": "desc",
                            "url": "https://example.com/image.png",
                            "coverUrl": None,
                            "sort": 1,
                        }
                    ],
                )
            )
            session.add(
                BenchmarkSample(
                    dataset_source_id=source.id,
                    sample_id=f"{self.prefix}_sample",
                    sample_name=f"{self.prefix} sample",
                    resource_path=f"{self.prefix}/resource",
                    entry_path="index.html",
                    user_goal="完成正常任务",
                    attacker_goal="诱导攻击",
                    attacker_is_user=False,
                    attack_delivery_type_id=delivery.id,
                    risk_subtype_id=subtype.id,
                    risk_level=2,
                    attack_level=2,
                    difficulty_seed=Decimal("0.500"),
                    difficulty_score=Decimal("0.500"),
                    asset_type_id=None,
                    expected_safe_behavior="拒绝攻击并完成正常任务",
                    is_active=True,
                )
            )
            session.commit()
        return dataset_code

    def seed_evaluation_run(self, *, user_id: int, dataset_code: str, status: str) -> str:
        with self.session() as session:
            subtype_row = session.execute(select(RiskSubtype.id, RiskSubtype.name).where(RiskSubtype.code == dataset_code)).one()
            now = datetime.now(timezone.utc)
            public_id = f"eval_{self.prefix}"
            run = TestRun(
                user_id=user_id,
                public_id=public_id,
                agent_name=f"{self.prefix} agent",
                description="评测烟测任务",
                submit_method="api",
                public_to_leaderboard=False,
                request_id=f"{self.prefix}_eval_request",
                agent_base_url="https://example.com/agent",
                credential_ref=None,
                status=status,
                sample_query_snapshot={"datasetIds": [dataset_code]},
                execution_config={"parameters": {"difficulty": 0.5, "timeoutMinutes": 20, "retryEnabled": False}},
                total_samples=1,
                completed_samples=0,
                success_count=0,
                failed_count=0,
                created_at=now,
                updated_at=now,
            )
            session.add(run)
            session.flush()
            session.add(
                RunDataset(
                    run_id=run.id,
                    dataset_code=dataset_code,
                    dataset_name=subtype_row.name,
                    order_no=1,
                    status=status,
                    total_samples=1,
                    completed_samples=0,
                )
            )
            session.commit()
        return public_id

    def cleanup(self) -> None:
        with self.session() as session:
            user_ids = list((session.execute(select(User.id).where(User.email.like(f"{self.prefix}%@example.com")))).scalars())
            run_ids = list(
                (
                    session.execute(
                        select(TestRun.id).where(
                            (TestRun.public_id.like(f"eval_{self.prefix}%")) | (TestRun.user_id.in_(user_ids) if user_ids else False)
                        )
                    )
                ).scalars()
            )
            subtype_ids = list((session.execute(select(RiskSubtype.id).where(RiskSubtype.code.like(f"{self.prefix}%")))).scalars())
            sample_ids: list[int] = []
            sample_execution_ids: list[int] = []

            if run_ids:
                sample_execution_ids = list((session.execute(select(SampleExecution.id).where(SampleExecution.run_id.in_(run_ids)))).scalars())
                score_ids = list((session.execute(select(EvaluationScore.id).where(EvaluationScore.run_id.in_(run_ids)))).scalars())
                if score_ids:
                    snapshot_ids = list(
                        (
                            session.execute(
                                select(LeaderboardEntry.snapshot_id).where(LeaderboardEntry.score_id.in_(score_ids))
                            )
                        ).scalars()
                    )
                    session.execute(delete(LeaderboardEntry).where(LeaderboardEntry.score_id.in_(score_ids)))
                    if snapshot_ids:
                        session.execute(delete(LeaderboardEntry).where(LeaderboardEntry.snapshot_id.in_(snapshot_ids)))
                        session.execute(delete(LeaderboardSnapshot).where(LeaderboardSnapshot.id.in_(snapshot_ids)))
                    session.execute(delete(EvaluationScore).where(EvaluationScore.id.in_(score_ids)))
                session.execute(delete(RunReport).where(RunReport.run_id.in_(run_ids)))
            if sample_execution_ids:
                session.execute(delete(ExecutionArtifact).where(ExecutionArtifact.sample_execution_id.in_(sample_execution_ids)))
                session.execute(delete(OracleResult).where(OracleResult.sample_execution_id.in_(sample_execution_ids)))
                session.execute(delete(ExecutionSummary).where(ExecutionSummary.sample_execution_id.in_(sample_execution_ids)))
                session.execute(delete(SampleExecution).where(SampleExecution.id.in_(sample_execution_ids)))
            if run_ids:
                session.execute(delete(RunSample).where(RunSample.run_id.in_(run_ids)))
                session.execute(delete(RunDataset).where(RunDataset.run_id.in_(run_ids)))
                session.execute(delete(TestRun).where(TestRun.id.in_(run_ids)))
            if user_ids:
                session.execute(delete(Agent).where(Agent.user_id.in_(user_ids)))
            if subtype_ids:
                sample_ids = list((session.execute(select(BenchmarkSample.id).where(BenchmarkSample.risk_subtype_id.in_(subtype_ids)))).scalars())
            if sample_ids:
                session.execute(delete(SampleDifficultyStat).where(SampleDifficultyStat.sample_id_ref.in_(sample_ids)))
                session.execute(delete(DifficultyVersionItem).where(DifficultyVersionItem.sample_id_ref.in_(sample_ids)))
                session.execute(delete(BenchmarkSample).where(BenchmarkSample.id.in_(sample_ids)))
            if subtype_ids:
                session.execute(delete(RiskSubtypeDisplayMeta).where(RiskSubtypeDisplayMeta.subtype_id.in_(subtype_ids)))
                session.execute(delete(RiskSubtype).where(RiskSubtype.id.in_(subtype_ids)))
            session.execute(delete(RiskCategory).where(RiskCategory.code.like(f"{self.prefix}%")))
            session.execute(delete(DatasetSource).where(DatasetSource.code.like(f"{self.prefix}%")))
            session.execute(delete(AttackDeliveryType).where(AttackDeliveryType.code.like(f"{self.prefix}%")))
            version_ids = list(
                (
                    session.execute(select(DifficultyVersion.id).where(DifficultyVersion.version_code.like(f"{self.prefix}%")))
                ).scalars()
            )
            if version_ids:
                session.execute(delete(DifficultyVersionItem).where(DifficultyVersionItem.version_id.in_(version_ids)))
                session.execute(delete(DifficultyVersion).where(DifficultyVersion.id.in_(version_ids)))
            if user_ids:
                session.execute(delete(User).where(User.id.in_(user_ids)))
            session.commit()

        for path in self.created_avatar_paths:
            if path.exists():
                path.unlink()


def png_bytes() -> bytes:
    """返回一个 1x1 PNG 文件内容，供头像上传与文件接口测试使用。"""
    image = io.BytesIO()
    image.write(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return image.getvalue()
