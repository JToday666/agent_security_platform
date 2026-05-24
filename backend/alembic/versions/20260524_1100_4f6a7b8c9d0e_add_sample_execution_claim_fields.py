"""add_sample_execution_claim_fields

Revision ID: 4f6a7b8c9d0e
Revises: 2b7c8d9e0f1a
Create Date: 2026-05-24 11:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f6a7b8c9d0e"
down_revision: Union[str, Sequence[str], None] = "2b7c8d9e0f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sample_executions", sa.Column("claimed_by", sa.Text(), nullable=True))
    op.add_column(
        "sample_executions",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "sample_executions",
        sa.Column("claim_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "sample_executions",
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "sample_executions",
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "sample_executions", sa.Column("attempt_reason", sa.Text(), nullable=True)
    )

    op.execute(
        "UPDATE sample_executions "
        "SET status = 'blocked', attempt_reason = COALESCE(attempt_reason, 'initial') "
        "WHERE status = 'pending'"
    )

    op.create_index(
        op.f("ix_sample_executions_claimed_by"),
        "sample_executions",
        ["claimed_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sample_executions_claim_heartbeat_at"),
        "sample_executions",
        ["claim_heartbeat_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sample_executions_lease_expires_at"),
        "sample_executions",
        ["lease_expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sample_executions_ready_at"),
        "sample_executions",
        ["ready_at"],
        unique=False,
    )
    op.create_index(
        "ix_sample_executions_ready_claim_lookup",
        "sample_executions",
        ["status", "ready_at", "lease_expires_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_sample_executions_claim_heartbeat",
        "sample_executions",
        ["claimed_by", "claim_heartbeat_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sample_executions_claim_heartbeat", table_name="sample_executions")
    op.drop_index(
        "ix_sample_executions_ready_claim_lookup", table_name="sample_executions"
    )
    op.drop_index(op.f("ix_sample_executions_ready_at"), table_name="sample_executions")
    op.drop_index(
        op.f("ix_sample_executions_lease_expires_at"), table_name="sample_executions"
    )
    op.drop_index(
        op.f("ix_sample_executions_claim_heartbeat_at"),
        table_name="sample_executions",
    )
    op.drop_index(
        op.f("ix_sample_executions_claimed_by"), table_name="sample_executions"
    )

    op.execute("UPDATE sample_executions SET status = 'pending' WHERE status = 'blocked'")

    op.drop_column("sample_executions", "attempt_reason")
    op.drop_column("sample_executions", "ready_at")
    op.drop_column("sample_executions", "lease_expires_at")
    op.drop_column("sample_executions", "claim_heartbeat_at")
    op.drop_column("sample_executions", "claimed_at")
    op.drop_column("sample_executions", "claimed_by")
