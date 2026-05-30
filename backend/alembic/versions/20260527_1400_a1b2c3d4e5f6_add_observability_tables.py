"""add observability event and audit tables

Revision ID: a1b2c3d4e5f6
Revises: 9e0f1a2b3c4d
Create Date: 2026-05-27 14:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a1b2c3d4e5f6"
down_revision = "9e0f1a2b3c4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sample_execution_events",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("sample_execution_id", sa.BigInteger(), nullable=True),
        sa.Column("sample_id", sa.Text(), nullable=True),
        sa.Column("worker_id", sa.Text(), nullable=True),
        sa.Column("runtime_session_id", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("level", sa.Text(), server_default=sa.text("'INFO'"), nullable=False),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["test_runs.id"],
            name=op.f("fk_sample_execution_events_run_id_test_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sample_execution_id"],
            ["sample_executions.id"],
            name=op.f("fk_sample_execution_events_sample_execution_id_sample_executions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sample_execution_events")),
    )
    op.create_index(
        "ix_sample_execution_events_event_type",
        "sample_execution_events",
        ["event_type"],
    )
    op.create_index(
        "ix_sample_execution_events_run_id",
        "sample_execution_events",
        ["run_id"],
    )
    op.create_index(
        "ix_sample_execution_events_run_occurred",
        "sample_execution_events",
        ["run_id", "occurred_at"],
    )
    op.create_index(
        "ix_sample_execution_events_sample_execution_id",
        "sample_execution_events",
        ["sample_execution_id"],
    )
    op.create_index(
        "ix_sample_execution_events_sample_occurred",
        "sample_execution_events",
        ["sample_execution_id", "occurred_at"],
    )
    op.create_index(
        "ix_sample_execution_events_occurred_at",
        "sample_execution_events",
        ["occurred_at"],
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_actor", "audit_logs", ["actor_type", "actor_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index(
        "ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_sample_execution_events_occurred_at", table_name="sample_execution_events")
    op.drop_index("ix_sample_execution_events_sample_occurred", table_name="sample_execution_events")
    op.drop_index(
        "ix_sample_execution_events_sample_execution_id",
        table_name="sample_execution_events",
    )
    op.drop_index("ix_sample_execution_events_run_occurred", table_name="sample_execution_events")
    op.drop_index("ix_sample_execution_events_run_id", table_name="sample_execution_events")
    op.drop_index("ix_sample_execution_events_event_type", table_name="sample_execution_events")
    op.drop_table("sample_execution_events")
