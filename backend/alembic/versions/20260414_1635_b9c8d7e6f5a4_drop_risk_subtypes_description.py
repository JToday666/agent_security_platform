"""drop_risk_subtypes_description

Revision ID: b9c8d7e6f5a4
Revises: 8c2f1b4d9e7a
Create Date: 2026-04-14 16:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9c8d7e6f5a4"
down_revision: Union[str, Sequence[str], None] = "8c2f1b4d9e7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("risk_subtypes", "description")


def downgrade() -> None:
    op.add_column(
        "risk_subtypes",
        sa.Column("description", sa.Text(), nullable=True, comment="相关背景资料及评测目的要求"),
    )
