"""create_agents

Revision ID: f1a2b3c4d5e6
Revises: b9c8d7e6f5a4
Create Date: 2026-04-28 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "b9c8d7e6f5a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("public_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("invoke_mode", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("connection", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("auth_type", sa.Text(), nullable=False),
        sa.Column("auth_public_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("credential_ref", sa.Text(), nullable=True),
        sa.Column("platform_input_mapping", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("task_render_mode", sa.Text(), nullable=False),
        sa.Column("custom_request_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("request_options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("platform_output_mapping", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("terminal_statuses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("success_statuses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verification_passed", sa.Boolean(), nullable=True),
        sa.Column("last_verification", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_agents_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agents")),
        sa.UniqueConstraint("public_id", name="uq_agents_public_id"),
    )
    op.create_index(op.f("ix_agents_user_id"), "agents", ["user_id"], unique=False)
    op.create_index(op.f("ix_agents_status"), "agents", ["status"], unique=False)
    op.create_index("ix_agents_user_id_status", "agents", ["user_id", "status"], unique=False)
    op.create_index("ix_agents_created_at", "agents", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agents_created_at", table_name="agents")
    op.drop_index("ix_agents_user_id_status", table_name="agents")
    op.drop_index(op.f("ix_agents_status"), table_name="agents")
    op.drop_index(op.f("ix_agents_user_id"), table_name="agents")
    op.drop_table("agents")
