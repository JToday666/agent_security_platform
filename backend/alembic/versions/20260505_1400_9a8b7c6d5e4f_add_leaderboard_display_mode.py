"""add_leaderboard_display_mode

Revision ID: 9a8b7c6d5e4f
Revises: 0f1e2d3c4b5a
Create Date: 2026-05-05 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a8b7c6d5e4f"
down_revision: Union[str, Sequence[str], None] = "0f1e2d3c4b5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "test_runs",
        sa.Column(
            "leaderboard_display_mode",
            sa.Text(),
            server_default=sa.text("'public'"),
            nullable=False,
            comment="排行榜展示模式(public/anonymous)",
        ),
    )
    op.create_check_constraint(
        "test_runs_leaderboard_display_mode_check",
        "test_runs",
        "leaderboard_display_mode IN ('public', 'anonymous')",
    )

    op.add_column("leaderboard_entries", sa.Column("display_name", sa.Text(), nullable=True))
    op.execute("UPDATE leaderboard_entries SET display_name = agent_name")
    op.alter_column("leaderboard_entries", "display_name", nullable=False)
    op.add_column(
        "leaderboard_entries",
        sa.Column("anonymous", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("leaderboard_entries", "anonymous")
    op.drop_column("leaderboard_entries", "display_name")
    op.drop_constraint("test_runs_leaderboard_display_mode_check", "test_runs", type_="check")
    op.drop_column("test_runs", "leaderboard_display_mode")
