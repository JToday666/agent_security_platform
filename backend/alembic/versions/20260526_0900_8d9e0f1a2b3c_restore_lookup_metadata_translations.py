"""restore_lookup_metadata_translations

Revision ID: 8d9e0f1a2b3c
Revises: 7c8d9e0f1a2b
Create Date: 2026-05-26 09:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "8d9e0f1a2b3c"
down_revision: Union[str, Sequence[str], None] = "7c8d9e0f1a2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    translation_column_type = postgresql.JSONB(astext_type=sa.Text())
    op.add_column(
        "dataset_sources",
        sa.Column(
            "translations",
            translation_column_type,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="按 locale 存储的数据源展示字段翻译",
        ),
    )
    op.add_column(
        "attack_delivery_types",
        sa.Column(
            "translations",
            translation_column_type,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="按 locale 存储的攻击投递方式展示字段翻译",
        ),
    )
    op.add_column(
        "asset_types",
        sa.Column(
            "translations",
            translation_column_type,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="按 locale 存储的资产类型展示字段翻译",
        ),
    )


def downgrade() -> None:
    op.drop_column("asset_types", "translations")
    op.drop_column("attack_delivery_types", "translations")
    op.drop_column("dataset_sources", "translations")
