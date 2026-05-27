"""add_agent_max_concurrency

Revision ID: 9e0f1a2b3c4d
Revises: 8d9e0f1a2b3c
Create Date: 2026-05-27 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9e0f1a2b3c4d"
down_revision: Union[str, Sequence[str], None] = "8d9e0f1a2b3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "max_concurrency",
            sa.Integer(),
            server_default=sa.text("4"),
            nullable=False,
            comment="该 Agent 允许同时运行的最大样本数",
        ),
    )


def downgrade() -> None:
    op.drop_column("agents", "max_concurrency")
