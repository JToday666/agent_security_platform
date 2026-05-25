"""add_runtime_sessions

Revision ID: 7c8d9e0f1a2b
Revises: 6b7c8d9e0f1a
Create Date: 2026-05-25 16:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c8d9e0f1a2b"
down_revision: Union[str, Sequence[str], None] = "6b7c8d9e0f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "runtime_sessions",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("sample_execution_id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("environment_ref", sa.Text(), nullable=False),
        sa.Column("internal_base_url", sa.Text(), nullable=False),
        sa.Column("public_entry_url", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'preparing'"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["test_runs.id"], name=op.f("fk_runtime_sessions_run_id_test_runs")
        ),
        sa.ForeignKeyConstraint(
            ["sample_execution_id"],
            ["sample_executions.id"],
            name=op.f("fk_runtime_sessions_sample_execution_id_sample_executions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_runtime_sessions")),
        sa.UniqueConstraint(
            "sample_execution_id",
            name=op.f("uq_runtime_sessions_sample_execution_id"),
        ),
    )
    op.create_index(
        op.f("ix_runtime_sessions_sample_execution_id"),
        "runtime_sessions",
        ["sample_execution_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_runtime_sessions_run_id"),
        "runtime_sessions",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_runtime_sessions_expires_at"),
        "runtime_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_runtime_sessions_status"),
        "runtime_sessions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_runtime_sessions_status_expires_at",
        "runtime_sessions",
        ["status", "expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_runtime_sessions_run_id_status",
        "runtime_sessions",
        ["run_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_runtime_sessions_run_id_status", table_name="runtime_sessions")
    op.drop_index("ix_runtime_sessions_status_expires_at", table_name="runtime_sessions")
    op.drop_index(op.f("ix_runtime_sessions_status"), table_name="runtime_sessions")
    op.drop_index(op.f("ix_runtime_sessions_expires_at"), table_name="runtime_sessions")
    op.drop_index(op.f("ix_runtime_sessions_run_id"), table_name="runtime_sessions")
    op.drop_index(
        op.f("ix_runtime_sessions_sample_execution_id"), table_name="runtime_sessions"
    )
    op.drop_table("runtime_sessions")
