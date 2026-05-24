"""add_worker_processes_and_claim_token

Revision ID: 5a6b7c8d9e0f
Revises: 4f6a7b8c9d0e
Create Date: 2026-05-24 13:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "5a6b7c8d9e0f"
down_revision: Union[str, Sequence[str], None] = "4f6a7b8c9d0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sample_executions", sa.Column("claim_token", sa.Text(), nullable=True))
    op.create_table(
        "worker_processes",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("worker_id", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("hostname", sa.Text(), nullable=False),
        sa.Column("pid", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'starting'"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "active_count", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_worker_processes")),
    )
    op.create_index(
        op.f("ix_worker_processes_worker_id"),
        "worker_processes",
        ["worker_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_worker_processes_role"), "worker_processes", ["role"], unique=False
    )
    op.create_index(
        op.f("ix_worker_processes_last_heartbeat_at"),
        "worker_processes",
        ["last_heartbeat_at"],
        unique=False,
    )
    op.create_index(
        "ix_worker_processes_role_status",
        "worker_processes",
        ["role", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_worker_processes_role_status", table_name="worker_processes")
    op.drop_index(
        op.f("ix_worker_processes_last_heartbeat_at"), table_name="worker_processes"
    )
    op.drop_index(op.f("ix_worker_processes_role"), table_name="worker_processes")
    op.drop_index(op.f("ix_worker_processes_worker_id"), table_name="worker_processes")
    op.drop_table("worker_processes")
    op.drop_column("sample_executions", "claim_token")
