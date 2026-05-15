"""评分、动态难度版本与排行榜 ORM 模型。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base


class DifficultyVersion(Base):
    """样本难度冻结版本。"""

    __tablename__ = "difficulty_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="difficulty_versions_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="难度版本主键"
    )
    version_code: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False, index=True, comment="难度版本编号"
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="draft",
        server_default=text("'draft'"),
        index=True,
    )
    base_version_code: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="基准版本编号"
    )
    algorithm_version: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="difficulty_calibration_v1",
        server_default=text("'difficulty_calibration_v1'"),
        comment="难度校准算法版本",
    )
    stats_cutoff_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="统计截止时间"
    )
    parameters: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    item_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DifficultyVersionItem(Base):
    """某个难度版本下的样本难度快照。"""

    __tablename__ = "difficulty_version_items"
    __table_args__ = (
        UniqueConstraint("version_id", "sample_id_ref"),
        Index("ix_difficulty_version_items_sample_id_ref", "sample_id_ref"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="难度版本条目主键"
    )
    version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("difficulty_versions.id"), nullable=False, index=True
    )
    sample_id_ref: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("benchmark_samples.id"), nullable=False
    )
    previous_difficulty_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False
    )
    candidate_completion_difficulty: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False
    )
    candidate_safety_difficulty: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False
    )
    candidate_difficulty_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False
    )
    completion_difficulty: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False
    )
    safety_difficulty: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    difficulty_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    valid_execution_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ScoreModelVersion(Base):
    """评分模型版本。"""

    __tablename__ = "score_model_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="score_model_versions_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    version_code: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="published", server_default=text("'published'")
    )
    parameters: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class BenchmarkVersion(Base):
    """评分使用的标准原型版本。"""

    __tablename__ = "benchmark_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="benchmark_versions_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    version_code: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="published", server_default=text("'published'")
    )
    parameters: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class BenchmarkVersionItem(Base):
    """标准原型集中的单个原型。"""

    __tablename__ = "benchmark_version_items"
    __table_args__ = (UniqueConstraint("version_id", "order_no"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("benchmark_versions.id"), nullable=False, index=True
    )
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_difficulty: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False
    )
    safety_difficulty: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    is_high_difficulty: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )


class EvaluationScore(Base):
    """单次评测的可复算评分结果。"""

    __tablename__ = "evaluation_scores"
    __table_args__ = (
        UniqueConstraint("run_id"),
        Index("ix_evaluation_scores_official_score", "official_conservative_score"),
        Index(
            "ix_evaluation_scores_certification_tier",
            "safety_certification",
            "verification_tier",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("test_runs.id"), nullable=False, index=True
    )
    score_model_version: Mapped[str] = mapped_column(Text, nullable=False)
    benchmark_version: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_version_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    theta_completion: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    theta_safety: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    variance_completion: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    variance_safety: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    official_conservative_score: Mapped[Decimal] = mapped_column(
        Numeric(7, 3), nullable=False
    )
    safe_capability_score: Mapped[Decimal] = mapped_column(
        Numeric(7, 3), nullable=False
    )
    completion_score: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    safety_score: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    unsafe_risk_score: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    high_difficulty_score: Mapped[Decimal] = mapped_column(
        Numeric(7, 3), nullable=False
    )
    operational_utility_score: Mapped[Decimal] = mapped_column(
        Numeric(7, 3), nullable=False
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    confidence_interval_low: Mapped[Decimal] = mapped_column(
        Numeric(7, 3), nullable=False
    )
    confidence_interval_high: Mapped[Decimal] = mapped_column(
        Numeric(7, 3), nullable=False
    )
    verification_tier: Mapped[str] = mapped_column(Text, nullable=False)
    safety_certification: Mapped[str] = mapped_column(Text, nullable=False)
    total_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_sample_count: Mapped[Decimal] = mapped_column(
        Numeric(8, 3), nullable=False
    )
    coverage: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    minor_violation_rate: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    major_violation_rate: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    critical_violation_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 5), nullable=False
    )
    score_payload: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )


class LeaderboardSnapshot(Base):
    """排行榜冻结快照。"""

    __tablename__ = "leaderboard_snapshots"
    __table_args__ = (
        CheckConstraint(
            "status IN ('published', 'archived')",
            name="leaderboard_snapshots_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    snapshot_code: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="published",
        server_default=text("'published'"),
        index=True,
    )
    score_model_version: Mapped[str] = mapped_column(Text, nullable=False)
    benchmark_version: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_version_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    entry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )


class LeaderboardEntry(Base):
    """排行榜快照条目。"""

    __tablename__ = "leaderboard_entries"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "rank_no"),
        UniqueConstraint("snapshot_id", "agent_id"),
        Index("ix_leaderboard_entries_snapshot_rank", "snapshot_id", "rank_no"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("leaderboard_snapshots.id"), nullable=False, index=True
    )
    score_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("evaluation_scores.id"), nullable=False, index=True
    )
    run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("test_runs.id"), nullable=False, index=True
    )
    rank_no: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    evaluation_id: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    anonymous: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    official_conservative_score: Mapped[Decimal] = mapped_column(
        Numeric(7, 3), nullable=False
    )
    safe_capability_score: Mapped[Decimal] = mapped_column(
        Numeric(7, 3), nullable=False
    )
    high_difficulty_score: Mapped[Decimal] = mapped_column(
        Numeric(7, 3), nullable=False
    )
    unsafe_risk_score: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    verification_tier: Mapped[str] = mapped_column(Text, nullable=False)
    safety_certification: Mapped[str] = mapped_column(Text, nullable=False)
    total_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
