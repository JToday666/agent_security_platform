"""set_sample_oracles_updated_at_default

Revision ID: 8c2f1b4d9e7a
Revises: a6b7c8d9e0f1
Create Date: 2026-04-09 22:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c2f1b4d9e7a"
down_revision: Union[str, Sequence[str], None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE sample_oracles
            SET updated_at = created_at
            WHERE updated_at IS NULL
            """
        )
    )
    op.alter_column(
        "sample_oracles",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "sample_oracles",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        nullable=True,
    )
