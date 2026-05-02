"""add_scoring_difficulty_leaderboards

Revision ID: 0f1e2d3c4b5a
Revises: f1a2b3c4d5e6
Create Date: 2026-05-03 01:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0f1e2d3c4b5a"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "run_samples",
        sa.Column("difficulty_version_code", sa.Text(), server_default=sa.text("'legacy_current'"), nullable=False),
    )
    op.add_column(
        "run_samples",
        sa.Column("difficulty_score_snapshot", sa.Numeric(4, 3), server_default=sa.text("0.500"), nullable=False),
    )
    op.add_column(
        "run_samples",
        sa.Column("completion_difficulty_snapshot", sa.Numeric(4, 3), server_default=sa.text("0.500"), nullable=False),
    )
    op.add_column(
        "run_samples",
        sa.Column("safety_difficulty_snapshot", sa.Numeric(4, 3), server_default=sa.text("0.500"), nullable=False),
    )

    op.add_column(
        "sample_difficulty_stats",
        sa.Column("completed_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "sample_difficulty_stats",
        sa.Column("unfinished_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "sample_difficulty_stats",
        sa.Column("minor_harm_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "sample_difficulty_stats",
        sa.Column("major_harm_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "sample_difficulty_stats",
        sa.Column("critical_harm_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "sample_difficulty_stats",
        sa.Column("candidate_completion_difficulty", sa.Numeric(4, 3), server_default=sa.text("0.500"), nullable=False),
    )
    op.add_column(
        "sample_difficulty_stats",
        sa.Column("candidate_safety_difficulty", sa.Numeric(4, 3), server_default=sa.text("0.500"), nullable=False),
    )
    op.add_column(
        "sample_difficulty_stats",
        sa.Column("candidate_difficulty_score", sa.Numeric(4, 3), server_default=sa.text("0.500"), nullable=False),
    )

    op.create_table(
        "difficulty_versions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("version_code", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("base_version_code", sa.Text(), nullable=True),
        sa.Column("algorithm_version", sa.Text(), server_default=sa.text("'difficulty_calibration_v1'"), nullable=False),
        sa.Column("stats_cutoff_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("item_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name=op.f("ck_difficulty_versions_status_check")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_difficulty_versions")),
    )
    op.create_index(op.f("ix_difficulty_versions_status"), "difficulty_versions", ["status"], unique=False)
    op.create_index(op.f("ix_difficulty_versions_version_code"), "difficulty_versions", ["version_code"], unique=True)

    op.create_table(
        "difficulty_version_items",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("version_id", sa.BigInteger(), nullable=False),
        sa.Column("sample_id_ref", sa.BigInteger(), nullable=False),
        sa.Column("previous_difficulty_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("candidate_completion_difficulty", sa.Numeric(4, 3), nullable=False),
        sa.Column("candidate_safety_difficulty", sa.Numeric(4, 3), nullable=False),
        sa.Column("candidate_difficulty_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("completion_difficulty", sa.Numeric(4, 3), nullable=False),
        sa.Column("safety_difficulty", sa.Numeric(4, 3), nullable=False),
        sa.Column("difficulty_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("valid_execution_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sample_id_ref"], ["benchmark_samples.id"], name=op.f("fk_difficulty_version_items_sample_id_ref_benchmark_samples")),
        sa.ForeignKeyConstraint(["version_id"], ["difficulty_versions.id"], name=op.f("fk_difficulty_version_items_version_id_difficulty_versions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_difficulty_version_items")),
        sa.UniqueConstraint("version_id", "sample_id_ref", name=op.f("uq_difficulty_version_items_version_id")),
    )
    op.create_index(op.f("ix_difficulty_version_items_sample_id_ref"), "difficulty_version_items", ["sample_id_ref"], unique=False)
    op.create_index(op.f("ix_difficulty_version_items_version_id"), "difficulty_version_items", ["version_id"], unique=False)

    op.create_table(
        "score_model_versions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("version_code", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'published'"), nullable=False),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name=op.f("ck_score_model_versions_status_check")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_score_model_versions")),
    )
    op.create_index(op.f("ix_score_model_versions_version_code"), "score_model_versions", ["version_code"], unique=True)

    op.create_table(
        "benchmark_versions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("version_code", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'published'"), nullable=False),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name=op.f("ck_benchmark_versions_status_check")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_benchmark_versions")),
    )
    op.create_index(op.f("ix_benchmark_versions_version_code"), "benchmark_versions", ["version_code"], unique=True)

    op.create_table(
        "benchmark_version_items",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("version_id", sa.BigInteger(), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.Column("completion_difficulty", sa.Numeric(4, 3), nullable=False),
        sa.Column("safety_difficulty", sa.Numeric(4, 3), nullable=False),
        sa.Column("weight", sa.Numeric(8, 6), nullable=False),
        sa.Column("is_high_difficulty", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["benchmark_versions.id"], name=op.f("fk_benchmark_version_items_version_id_benchmark_versions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_benchmark_version_items")),
        sa.UniqueConstraint("version_id", "order_no", name=op.f("uq_benchmark_version_items_version_id")),
    )
    op.create_index(op.f("ix_benchmark_version_items_version_id"), "benchmark_version_items", ["version_id"], unique=False)

    op.create_table(
        "evaluation_scores",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("score_model_version", sa.Text(), nullable=False),
        sa.Column("benchmark_version", sa.Text(), nullable=False),
        sa.Column("difficulty_version_code", sa.Text(), nullable=True),
        sa.Column("theta_completion", sa.Numeric(10, 6), nullable=False),
        sa.Column("theta_safety", sa.Numeric(10, 6), nullable=False),
        sa.Column("variance_completion", sa.Numeric(10, 6), nullable=False),
        sa.Column("variance_safety", sa.Numeric(10, 6), nullable=False),
        sa.Column("official_conservative_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("safe_capability_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("completion_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("safety_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("unsafe_risk_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("high_difficulty_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("operational_utility_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("confidence", sa.Numeric(7, 3), nullable=False),
        sa.Column("confidence_interval_low", sa.Numeric(7, 3), nullable=False),
        sa.Column("confidence_interval_high", sa.Numeric(7, 3), nullable=False),
        sa.Column("verification_tier", sa.Text(), nullable=False),
        sa.Column("safety_certification", sa.Text(), nullable=False),
        sa.Column("total_samples", sa.Integer(), nullable=False),
        sa.Column("effective_sample_count", sa.Numeric(8, 3), nullable=False),
        sa.Column("coverage", sa.Numeric(6, 5), nullable=False),
        sa.Column("minor_violation_rate", sa.Numeric(6, 5), nullable=False),
        sa.Column("major_violation_rate", sa.Numeric(6, 5), nullable=False),
        sa.Column("critical_violation_rate", sa.Numeric(6, 5), nullable=False),
        sa.Column("score_payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["test_runs.id"], name=op.f("fk_evaluation_scores_run_id_test_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_scores")),
        sa.UniqueConstraint("run_id", name=op.f("uq_evaluation_scores_run_id")),
    )
    op.create_index(op.f("ix_evaluation_scores_certification_tier"), "evaluation_scores", ["safety_certification", "verification_tier"], unique=False)
    op.create_index(op.f("ix_evaluation_scores_official_score"), "evaluation_scores", ["official_conservative_score"], unique=False)
    op.create_index(op.f("ix_evaluation_scores_run_id"), "evaluation_scores", ["run_id"], unique=False)

    op.create_table(
        "leaderboard_snapshots",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_code", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'published'"), nullable=False),
        sa.Column("score_model_version", sa.Text(), nullable=False),
        sa.Column("benchmark_version", sa.Text(), nullable=False),
        sa.Column("difficulty_version_code", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("entry_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.CheckConstraint("status IN ('published', 'archived')", name=op.f("ck_leaderboard_snapshots_status_check")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_leaderboard_snapshots")),
    )
    op.create_index(op.f("ix_leaderboard_snapshots_snapshot_code"), "leaderboard_snapshots", ["snapshot_code"], unique=True)
    op.create_index(op.f("ix_leaderboard_snapshots_status"), "leaderboard_snapshots", ["status"], unique=False)

    op.create_table(
        "leaderboard_entries",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_id", sa.BigInteger(), nullable=False),
        sa.Column("score_id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("rank_no", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Text(), nullable=False),
        sa.Column("agent_name", sa.Text(), nullable=False),
        sa.Column("evaluation_id", sa.Text(), nullable=False),
        sa.Column("official_conservative_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("safe_capability_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("high_difficulty_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("unsafe_risk_score", sa.Numeric(7, 3), nullable=False),
        sa.Column("confidence", sa.Numeric(7, 3), nullable=False),
        sa.Column("verification_tier", sa.Text(), nullable=False),
        sa.Column("safety_certification", sa.Text(), nullable=False),
        sa.Column("total_samples", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["test_runs.id"], name=op.f("fk_leaderboard_entries_run_id_test_runs")),
        sa.ForeignKeyConstraint(["score_id"], ["evaluation_scores.id"], name=op.f("fk_leaderboard_entries_score_id_evaluation_scores")),
        sa.ForeignKeyConstraint(["snapshot_id"], ["leaderboard_snapshots.id"], name=op.f("fk_leaderboard_entries_snapshot_id_leaderboard_snapshots")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_leaderboard_entries")),
        sa.UniqueConstraint("snapshot_id", "agent_id", name=op.f("uq_leaderboard_entries_snapshot_id")),
        sa.UniqueConstraint("snapshot_id", "rank_no", name=op.f("uq_leaderboard_entries_snapshot_rank")),
    )
    op.create_index(op.f("ix_leaderboard_entries_agent_id"), "leaderboard_entries", ["agent_id"], unique=False)
    op.create_index(op.f("ix_leaderboard_entries_run_id"), "leaderboard_entries", ["run_id"], unique=False)
    op.create_index(op.f("ix_leaderboard_entries_score_id"), "leaderboard_entries", ["score_id"], unique=False)
    op.create_index(op.f("ix_leaderboard_entries_snapshot_id"), "leaderboard_entries", ["snapshot_id"], unique=False)
    op.create_index(op.f("ix_leaderboard_entries_snapshot_rank"), "leaderboard_entries", ["snapshot_id", "rank_no"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_leaderboard_entries_snapshot_rank"), table_name="leaderboard_entries")
    op.drop_index(op.f("ix_leaderboard_entries_snapshot_id"), table_name="leaderboard_entries")
    op.drop_index(op.f("ix_leaderboard_entries_score_id"), table_name="leaderboard_entries")
    op.drop_index(op.f("ix_leaderboard_entries_run_id"), table_name="leaderboard_entries")
    op.drop_index(op.f("ix_leaderboard_entries_agent_id"), table_name="leaderboard_entries")
    op.drop_table("leaderboard_entries")

    op.drop_index(op.f("ix_leaderboard_snapshots_status"), table_name="leaderboard_snapshots")
    op.drop_index(op.f("ix_leaderboard_snapshots_snapshot_code"), table_name="leaderboard_snapshots")
    op.drop_table("leaderboard_snapshots")

    op.drop_index(op.f("ix_evaluation_scores_run_id"), table_name="evaluation_scores")
    op.drop_index(op.f("ix_evaluation_scores_official_score"), table_name="evaluation_scores")
    op.drop_index(op.f("ix_evaluation_scores_certification_tier"), table_name="evaluation_scores")
    op.drop_table("evaluation_scores")

    op.drop_index(op.f("ix_benchmark_version_items_version_id"), table_name="benchmark_version_items")
    op.drop_table("benchmark_version_items")
    op.drop_index(op.f("ix_benchmark_versions_version_code"), table_name="benchmark_versions")
    op.drop_table("benchmark_versions")

    op.drop_index(op.f("ix_score_model_versions_version_code"), table_name="score_model_versions")
    op.drop_table("score_model_versions")

    op.drop_index(op.f("ix_difficulty_version_items_version_id"), table_name="difficulty_version_items")
    op.drop_index(op.f("ix_difficulty_version_items_sample_id_ref"), table_name="difficulty_version_items")
    op.drop_table("difficulty_version_items")
    op.drop_index(op.f("ix_difficulty_versions_version_code"), table_name="difficulty_versions")
    op.drop_index(op.f("ix_difficulty_versions_status"), table_name="difficulty_versions")
    op.drop_table("difficulty_versions")

    op.drop_column("sample_difficulty_stats", "candidate_difficulty_score")
    op.drop_column("sample_difficulty_stats", "candidate_safety_difficulty")
    op.drop_column("sample_difficulty_stats", "candidate_completion_difficulty")
    op.drop_column("sample_difficulty_stats", "critical_harm_count")
    op.drop_column("sample_difficulty_stats", "major_harm_count")
    op.drop_column("sample_difficulty_stats", "minor_harm_count")
    op.drop_column("sample_difficulty_stats", "unfinished_count")
    op.drop_column("sample_difficulty_stats", "completed_count")

    op.drop_column("run_samples", "safety_difficulty_snapshot")
    op.drop_column("run_samples", "completion_difficulty_snapshot")
    op.drop_column("run_samples", "difficulty_score_snapshot")
    op.drop_column("run_samples", "difficulty_version_code")
