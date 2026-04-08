"""create_sample_execution_tables

Revision ID: c4d6e8f0a2b3
Revises: a3c5e7f9b1d2
Create Date: 2026-04-08 10:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c4d6e8f0a2b3"
down_revision: Union[str, Sequence[str], None] = "a3c5e7f9b1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sample_executions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("run_sample_id", sa.BigInteger(), nullable=False),
        sa.Column("sample_id_ref", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("retry_no", sa.SmallInteger(), nullable=False),
        sa.Column("work_dir", sa.Text(), nullable=True),
        sa.Column("entry_url", sa.Text(), nullable=True),
        sa.Column("environment_ref", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["test_runs.id"],
            name=op.f("fk_sample_executions_run_id_test_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["run_sample_id"],
            ["run_samples.id"],
            name=op.f("fk_sample_executions_run_sample_id_run_samples"),
        ),
        sa.ForeignKeyConstraint(
            ["sample_id_ref"],
            ["benchmark_samples.id"],
            name=op.f("fk_sample_executions_sample_id_ref_benchmark_samples"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sample_executions")),
        sa.UniqueConstraint(
            "run_sample_id",
            "retry_no",
            name=op.f("uq_sample_executions_run_sample_id"),
        ),
    )
    op.create_index(
        op.f("ix_sample_executions_created_at"),
        "sample_executions",
        ["created_at"],
        unique=False,
    )
    op.create_index(op.f("ix_sample_executions_run_id"), "sample_executions", ["run_id"], unique=False)
    op.create_index(
        "ix_sample_executions_run_id_status",
        "sample_executions",
        ["run_id", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sample_executions_run_sample_id"),
        "sample_executions",
        ["run_sample_id"],
        unique=False,
    )
    op.create_index(
        "ix_sample_executions_run_sample_id_retry_no",
        "sample_executions",
        ["run_sample_id", "retry_no"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sample_executions_sample_id_ref"),
        "sample_executions",
        ["sample_id_ref"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sample_executions_status"),
        "sample_executions",
        ["status"],
        unique=False,
    )

    op.create_table(
        "execution_artifacts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("sample_execution_id", sa.BigInteger(), nullable=False),
        sa.Column("artifact_type", sa.Text(), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["sample_execution_id"],
            ["sample_executions.id"],
            name=op.f("fk_execution_artifacts_sample_execution_id_sample_executions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_execution_artifacts")),
    )
    op.create_index(
        op.f("ix_execution_artifacts_sample_execution_id"),
        "execution_artifacts",
        ["sample_execution_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_artifacts_sample_execution_id_artifact_type",
        "execution_artifacts",
        ["sample_execution_id", "artifact_type"],
        unique=False,
    )

    op.create_table(
        "oracle_results",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("sample_execution_id", sa.BigInteger(), nullable=False),
        sa.Column("oracle_id", sa.BigInteger(), nullable=False),
        sa.Column("matched", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Numeric(4, 3), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("evidence_ref", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("evaluator_version", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("score >= 0 AND score <= 1", name=op.f("ck_oracle_results_score_range")),
        sa.ForeignKeyConstraint(
            ["oracle_id"],
            ["sample_oracles.id"],
            name=op.f("fk_oracle_results_oracle_id_sample_oracles"),
        ),
        sa.ForeignKeyConstraint(
            ["sample_execution_id"],
            ["sample_executions.id"],
            name=op.f("fk_oracle_results_sample_execution_id_sample_executions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oracle_results")),
        sa.UniqueConstraint(
            "sample_execution_id",
            "oracle_id",
            name=op.f("uq_oracle_results_sample_execution_id"),
        ),
    )
    op.create_index(
        op.f("ix_oracle_results_oracle_id"),
        "oracle_results",
        ["oracle_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_oracle_results_sample_execution_id"),
        "oracle_results",
        ["sample_execution_id"],
        unique=False,
    )
    op.create_index(
        "ix_oracle_results_sample_execution_id_matched",
        "oracle_results",
        ["sample_execution_id", "matched"],
        unique=False,
    )

    op.create_table(
        "execution_summaries",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("sample_execution_id", sa.BigInteger(), nullable=False),
        sa.Column("task_completed", sa.Boolean(), nullable=False),
        sa.Column("harm_detected", sa.Boolean(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("final_label", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["sample_execution_id"],
            ["sample_executions.id"],
            name=op.f("fk_execution_summaries_sample_execution_id_sample_executions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_execution_summaries")),
        sa.UniqueConstraint(
            "sample_execution_id",
            name=op.f("uq_execution_summaries_sample_execution_id"),
        ),
    )
    op.create_index(
        op.f("ix_execution_summaries_sample_execution_id"),
        "execution_summaries",
        ["sample_execution_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_summaries_task_completed_harm_detected",
        "execution_summaries",
        ["task_completed", "harm_detected"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_execution_summaries_task_completed_harm_detected",
        table_name="execution_summaries",
    )
    op.drop_index(
        op.f("ix_execution_summaries_sample_execution_id"),
        table_name="execution_summaries",
    )
    op.drop_table("execution_summaries")

    op.drop_index(
        "ix_oracle_results_sample_execution_id_matched",
        table_name="oracle_results",
    )
    op.drop_index(op.f("ix_oracle_results_sample_execution_id"), table_name="oracle_results")
    op.drop_index(op.f("ix_oracle_results_oracle_id"), table_name="oracle_results")
    op.drop_table("oracle_results")

    op.drop_index(
        "ix_execution_artifacts_sample_execution_id_artifact_type",
        table_name="execution_artifacts",
    )
    op.drop_index(
        op.f("ix_execution_artifacts_sample_execution_id"),
        table_name="execution_artifacts",
    )
    op.drop_table("execution_artifacts")

    op.drop_index(op.f("ix_sample_executions_status"), table_name="sample_executions")
    op.drop_index(op.f("ix_sample_executions_sample_id_ref"), table_name="sample_executions")
    op.drop_index(
        "ix_sample_executions_run_sample_id_retry_no",
        table_name="sample_executions",
    )
    op.drop_index(op.f("ix_sample_executions_run_sample_id"), table_name="sample_executions")
    op.drop_index("ix_sample_executions_run_id_status", table_name="sample_executions")
    op.drop_index(op.f("ix_sample_executions_run_id"), table_name="sample_executions")
    op.drop_index(op.f("ix_sample_executions_created_at"), table_name="sample_executions")
    op.drop_table("sample_executions")
