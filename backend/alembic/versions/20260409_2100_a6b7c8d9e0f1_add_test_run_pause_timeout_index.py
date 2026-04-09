"""add_test_run_pause_timeout_index

Revision ID: a6b7c8d9e0f1
Revises: d1f2e3a4b5c6
Create Date: 2026-04-09 21:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, Sequence[str], None] = "d1f2e3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_test_runs_status_pause_deadline_at",
        "test_runs",
        ["status", "pause_deadline_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_test_runs_status_pause_deadline_at", table_name="test_runs")
