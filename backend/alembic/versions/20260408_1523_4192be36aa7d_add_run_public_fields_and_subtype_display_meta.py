"""add_run_public_fields_and_subtype_display_meta

Revision ID: 4192be36aa7d
Revises: e5f7a9b1c3d4
Create Date: 2026-04-08 15:23:28.970093
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4192be36aa7d'
down_revision: Union[str, Sequence[str], None] = 'e5f7a9b1c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("risk_categories", sa.Column("meaning", sa.Text(), nullable=True))
    op.add_column(
        "risk_categories",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.execute(sa.text("UPDATE risk_categories SET updated_at = created_at"))

    op.create_table(
        "risk_subtype_display_meta",
        sa.Column("subtype_id", sa.Integer(), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("full_description", sa.Text(), nullable=True),
        sa.Column(
            "highlights",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "scenarios",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "resources",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "media",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subtype_id"],
            ["risk_subtypes.id"],
            name=op.f("fk_risk_subtype_display_meta_subtype_id_risk_subtypes"),
        ),
        sa.PrimaryKeyConstraint("subtype_id", name=op.f("pk_risk_subtype_display_meta")),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO risk_subtype_display_meta (subtype_id)
            SELECT id
            FROM risk_subtypes
            """
        )
    )

    op.add_column(
        "sample_executions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE sample_executions
            SET updated_at = COALESCE(finished_at, started_at, created_at)
            """
        )
    )

    op.add_column("test_runs", sa.Column("public_id", sa.Text(), nullable=True))
    op.add_column("test_runs", sa.Column("agent_name", sa.Text(), nullable=True))
    op.add_column("test_runs", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("test_runs", sa.Column("submit_method", sa.Text(), nullable=True))
    op.add_column(
        "test_runs",
        sa.Column(
            "public_to_leaderboard",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )
    op.add_column("test_runs", sa.Column("request_id", sa.Text(), nullable=True))
    op.add_column(
        "test_runs",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column("test_runs", sa.Column("finalization_reason", sa.Text(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE test_runs
            SET
                public_id = 'eval_' || id::text,
                agent_name = '未命名智能体',
                submit_method = 'api',
                request_id = 'legacy_' || id::text,
                updated_at = COALESCE(finished_at, started_at, created_at),
                finalization_reason = CASE status
                    WHEN 'completed' THEN 'completed'
                    WHEN 'failed' THEN 'failed'
                    WHEN 'cancelled' THEN 'canceled_by_user'
                    ELSE NULL
                END
            """
        )
    )

    op.alter_column("test_runs", "public_id", existing_type=sa.Text(), nullable=False)
    op.alter_column("test_runs", "agent_name", existing_type=sa.Text(), nullable=False)
    op.alter_column("test_runs", "submit_method", existing_type=sa.Text(), nullable=False)
    op.alter_column("test_runs", "request_id", existing_type=sa.Text(), nullable=False)

    op.create_index(
        "ix_test_runs_status_updated_at",
        "test_runs",
        ["status", "updated_at"],
        unique=False,
    )
    op.create_unique_constraint(op.f("uq_test_runs_public_id"), "test_runs", ["public_id"])
    op.create_unique_constraint(
        op.f("uq_test_runs_user_id"),
        "test_runs",
        ["user_id", "request_id"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_test_runs_user_id"), "test_runs", type_="unique")
    op.drop_constraint(op.f("uq_test_runs_public_id"), "test_runs", type_="unique")
    op.drop_index("ix_test_runs_status_updated_at", table_name="test_runs")
    op.drop_column("test_runs", "finalization_reason")
    op.drop_column("test_runs", "updated_at")
    op.drop_column("test_runs", "request_id")
    op.drop_column("test_runs", "public_to_leaderboard")
    op.drop_column("test_runs", "submit_method")
    op.drop_column("test_runs", "description")
    op.drop_column("test_runs", "agent_name")
    op.drop_column("test_runs", "public_id")
    op.drop_column("sample_executions", "updated_at")
    op.drop_table("risk_subtype_display_meta")
    op.drop_column("risk_categories", "updated_at")
    op.drop_column("risk_categories", "meaning")
