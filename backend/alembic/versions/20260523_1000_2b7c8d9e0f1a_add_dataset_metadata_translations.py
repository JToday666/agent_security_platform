"""add_dataset_metadata_translations

Revision ID: 2b7c8d9e0f1a
Revises: 9a8b7c6d5e4f
Create Date: 2026-05-23 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2b7c8d9e0f1a"
down_revision: Union[str, Sequence[str], None] = "9a8b7c6d5e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    translation_column_type = postgresql.JSONB(astext_type=sa.Text())
    op.add_column(
        "risk_categories",
        sa.Column(
            "translations",
            translation_column_type,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="按 locale 存储的风险大类展示字段翻译",
        ),
    )
    op.add_column(
        "risk_subtypes",
        sa.Column(
            "translations",
            translation_column_type,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="按 locale 存储的风险子类展示字段翻译",
        ),
    )
    op.add_column(
        "risk_subtype_display_meta",
        sa.Column(
            "translations",
            translation_column_type,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="按 locale 存储的展示元数据翻译",
        ),
    )


def downgrade() -> None:
    op.drop_column("risk_subtype_display_meta", "translations")
    op.drop_column("risk_subtypes", "translations")
    op.drop_column("risk_categories", "translations")
