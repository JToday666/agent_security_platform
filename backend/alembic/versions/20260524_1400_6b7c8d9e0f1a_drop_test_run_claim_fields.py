"""drop_test_run_claim_fields

Revision ID: 6b7c8d9e0f1a
Revises: 5a6b7c8d9e0f
Create Date: 2026-05-24 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6b7c8d9e0f1a"
down_revision: Union[str, Sequence[str], None] = "5a6b7c8d9e0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_test_runs_worker_claim_lookup", table_name="test_runs")
    op.drop_index(op.f("ix_test_runs_claim_heartbeat_at"), table_name="test_runs")
    op.drop_index(op.f("ix_test_runs_claimed_by"), table_name="test_runs")
    op.drop_column("test_runs", "claim_heartbeat_at")
    op.drop_column("test_runs", "claimed_at")
    op.drop_column("test_runs", "claimed_by")


def downgrade() -> None:
    op.add_column("test_runs", sa.Column("claimed_by", sa.Text(), nullable=True))
    op.add_column(
        "test_runs", sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "test_runs",
        sa.Column("claim_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_test_runs_claimed_by"),
        "test_runs",
        ["claimed_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_test_runs_claim_heartbeat_at"),
        "test_runs",
        ["claim_heartbeat_at"],
        unique=False,
    )
    op.create_index(
        "ix_test_runs_worker_claim_lookup",
        "test_runs",
        ["status", "claimed_by", "claim_heartbeat_at", "created_at"],
        unique=False,
    )

