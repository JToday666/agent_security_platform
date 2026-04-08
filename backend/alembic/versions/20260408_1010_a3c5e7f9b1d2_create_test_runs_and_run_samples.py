"""create_test_runs_and_run_samples

Revision ID: a3c5e7f9b1d2
Revises: 91e6a8d2c3f4
Create Date: 2026-04-08 10:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a3c5e7f9b1d2"
down_revision: Union[str, Sequence[str], None] = "91e6a8d2c3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_runs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("agent_base_url", sa.Text(), nullable=False),
        sa.Column("credential_ref", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "sample_query_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("execution_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("total_samples", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("completed_samples", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("success_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_test_runs_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_runs")),
    )
    op.create_index(op.f("ix_test_runs_created_at"), "test_runs", ["created_at"], unique=False)
    op.create_index(op.f("ix_test_runs_status"), "test_runs", ["status"], unique=False)
    op.create_index(op.f("ix_test_runs_user_id"), "test_runs", ["user_id"], unique=False)

    op.create_table(
        "run_samples",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("sample_id_ref", sa.BigInteger(), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["test_runs.id"],
            name=op.f("fk_run_samples_run_id_test_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["sample_id_ref"],
            ["benchmark_samples.id"],
            name=op.f("fk_run_samples_sample_id_ref_benchmark_samples"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_samples")),
        sa.UniqueConstraint("run_id", "sample_id_ref", name=op.f("uq_run_samples_run_id")),
    )
    op.create_index(op.f("ix_run_samples_run_id"), "run_samples", ["run_id"], unique=False)
    op.create_index(
        op.f("ix_run_samples_sample_id_ref"),
        "run_samples",
        ["sample_id_ref"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_run_samples_sample_id_ref"), table_name="run_samples")
    op.drop_index(op.f("ix_run_samples_run_id"), table_name="run_samples")
    op.drop_table("run_samples")

    op.drop_index(op.f("ix_test_runs_user_id"), table_name="test_runs")
    op.drop_index(op.f("ix_test_runs_status"), table_name="test_runs")
    op.drop_index(op.f("ix_test_runs_created_at"), table_name="test_runs")
    op.drop_table("test_runs")
