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
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TestRun(Base):
    __tablename__ = "test_runs"
    __table_args__ = (
        UniqueConstraint("user_id", "request_id"),
        Index("ix_test_runs_status_updated_at", "status", "updated_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    public_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    submit_method: Mapped[str] = mapped_column(Text, nullable=False)
    public_to_leaderboard: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    request_id: Mapped[str] = mapped_column(Text, nullable=False)
    agent_base_url: Mapped[str] = mapped_column(Text, nullable=False)
    credential_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    sample_query_snapshot: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    execution_config: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    total_samples: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    completed_samples: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finalization_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class RunSample(Base):
    __tablename__ = "run_samples"
    __table_args__ = (
        UniqueConstraint("run_id", "sample_id_ref"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("test_runs.id"),
        nullable=False,
        index=True,
    )
    sample_id_ref: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("benchmark_samples.id"),
        nullable=False,
        index=True,
    )
    order_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class SampleExecution(Base):
    __tablename__ = "sample_executions"
    __table_args__ = (
        UniqueConstraint("run_sample_id", "retry_no"),
        Index("ix_sample_executions_run_id_status", "run_id", "status"),
        Index(
            "ix_sample_executions_run_sample_id_retry_no",
            "run_sample_id",
            "retry_no",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("test_runs.id"),
        nullable=False,
        index=True,
    )
    run_sample_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("run_samples.id"),
        nullable=False,
        index=True,
    )
    sample_id_ref: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("benchmark_samples.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    retry_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    work_dir: Mapped[str | None] = mapped_column(Text, nullable=True)
    entry_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ExecutionArtifact(Base):
    __tablename__ = "execution_artifacts"
    __table_args__ = (
        Index(
            "ix_execution_artifacts_sample_execution_id_artifact_type",
            "sample_execution_id",
            "artifact_type",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sample_execution_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sample_executions.id"),
        nullable=False,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(Text, nullable=False)
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_metadata: Mapped[dict[str, object] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class OracleResult(Base):
    __tablename__ = "oracle_results"
    __table_args__ = (
        UniqueConstraint("sample_execution_id", "oracle_id"),
        CheckConstraint("score >= 0 AND score <= 1", name="score_range"),
        Index(
            "ix_oracle_results_sample_execution_id_matched",
            "sample_execution_id",
            "matched",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sample_execution_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sample_executions.id"),
        nullable=False,
        index=True,
    )
    oracle_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sample_oracles.id"),
        nullable=False,
        index=True,
    )
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_ref: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    evaluator_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class ExecutionSummary(Base):
    __tablename__ = "execution_summaries"
    __table_args__ = (
        UniqueConstraint("sample_execution_id"),
        Index(
            "ix_execution_summaries_task_completed_harm_detected",
            "task_completed",
            "harm_detected",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sample_execution_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("sample_executions.id"),
        nullable=False,
        index=True,
    )
    task_completed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    harm_detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class SampleDifficultyStat(Base):
    __tablename__ = "sample_difficulty_stats"
    __table_args__ = (
        CheckConstraint(
            "valid_execution_count >= 0",
            name="valid_execution_count_nonnegative",
        ),
        CheckConstraint("harm_count >= 0", name="harm_count_nonnegative"),
        CheckConstraint(
            "safe_completion_count >= 0",
            name="safe_completion_count_nonnegative",
        ),
        CheckConstraint("harm_rate >= 0 AND harm_rate <= 1", name="harm_rate_range"),
        CheckConstraint(
            "safe_completion_rate >= 0 AND safe_completion_rate <= 1",
            name="safe_completion_rate_range",
        ),
        CheckConstraint(
            "inferred_difficulty >= 0 AND inferred_difficulty <= 1",
            name="inferred_difficulty_range",
        ),
    )

    sample_id_ref: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("benchmark_samples.id"),
        primary_key=True,
    )
    valid_execution_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    harm_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    safe_completion_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    harm_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    safe_completion_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    inferred_difficulty: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(Text, nullable=False)
    last_execution_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )


class RunReport(Base):
    __tablename__ = "run_reports"
    __table_args__ = (
        UniqueConstraint("run_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("test_runs.id"),
        nullable=False,
        index=True,
    )
    report_status: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    summary_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    report_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
