"""create_run_reports_and_sample_difficulty_stats

Revision ID: e5f7a9b1c3d4
Revises: c4d6e8f0a2b3
Create Date: 2026-04-08 10:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e5f7a9b1c3d4"
down_revision: Union[str, Sequence[str], None] = "c4d6e8f0a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "run_reports",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("report_status", sa.Text(), nullable=False),
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("report_uri", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["test_runs.id"],
            name=op.f("fk_run_reports_run_id_test_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_reports")),
        sa.UniqueConstraint("run_id", name=op.f("uq_run_reports_run_id")),
    )
    op.create_index(op.f("ix_run_reports_report_status"), "run_reports", ["report_status"], unique=False)
    op.create_index(op.f("ix_run_reports_run_id"), "run_reports", ["run_id"], unique=False)

    op.create_table(
        "sample_difficulty_stats",
        sa.Column("sample_id_ref", sa.BigInteger(), nullable=False),
        sa.Column("valid_execution_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("harm_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("safe_completion_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("harm_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("safe_completion_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("inferred_difficulty", sa.Numeric(4, 3), nullable=False),
        sa.Column("algorithm_version", sa.Text(), nullable=False),
        sa.Column("last_execution_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "harm_count >= 0",
            name=op.f("ck_sample_difficulty_stats_harm_count_nonnegative"),
        ),
        sa.CheckConstraint(
            "harm_rate >= 0 AND harm_rate <= 1",
            name=op.f("ck_sample_difficulty_stats_harm_rate_range"),
        ),
        sa.CheckConstraint(
            "inferred_difficulty >= 0 AND inferred_difficulty <= 1",
            name=op.f("ck_sample_difficulty_stats_inferred_difficulty_range"),
        ),
        sa.CheckConstraint(
            "safe_completion_count >= 0",
            name=op.f("ck_sample_difficulty_stats_safe_completion_count_nonnegative"),
        ),
        sa.CheckConstraint(
            "safe_completion_rate >= 0 AND safe_completion_rate <= 1",
            name=op.f("ck_sample_difficulty_stats_safe_completion_rate_range"),
        ),
        sa.CheckConstraint(
            "valid_execution_count >= 0",
            name=op.f("ck_sample_difficulty_stats_valid_execution_count_nonnegative"),
        ),
        sa.ForeignKeyConstraint(
            ["sample_id_ref"],
            ["benchmark_samples.id"],
            name=op.f("fk_sample_difficulty_stats_sample_id_ref_benchmark_samples"),
        ),
        sa.PrimaryKeyConstraint("sample_id_ref", name=op.f("pk_sample_difficulty_stats")),
    )
    op.create_index(
        op.f("ix_sample_difficulty_stats_last_execution_at"),
        "sample_difficulty_stats",
        ["last_execution_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sample_difficulty_stats_updated_at"),
        "sample_difficulty_stats",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_sample_difficulty_stats_updated_at"),
        table_name="sample_difficulty_stats",
    )
    op.drop_index(
        op.f("ix_sample_difficulty_stats_last_execution_at"),
        table_name="sample_difficulty_stats",
    )
    op.drop_table("sample_difficulty_stats")

    op.drop_index(op.f("ix_run_reports_run_id"), table_name="run_reports")
    op.drop_index(op.f("ix_run_reports_report_status"), table_name="run_reports")
    op.drop_table("run_reports")
