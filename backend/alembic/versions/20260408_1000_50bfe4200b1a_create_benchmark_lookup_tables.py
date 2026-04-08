"""create_benchmark_lookup_tables

Revision ID: 50bfe4200b1a
Revises: 6dbccc598a4b
Create Date: 2026-04-08 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "50bfe4200b1a"
down_revision: Union[str, Sequence[str], None] = "6dbccc598a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dataset_sources",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset_sources")),
    )
    op.create_index(op.f("ix_dataset_sources_code"), "dataset_sources", ["code"], unique=True)

    op.create_table(
        "attack_delivery_types",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attack_delivery_types")),
    )
    op.create_index(
        op.f("ix_attack_delivery_types_code"),
        "attack_delivery_types",
        ["code"],
        unique=True,
    )

    op.create_table(
        "risk_categories",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.SmallInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_risk_categories")),
    )
    op.create_index(op.f("ix_risk_categories_code"), "risk_categories", ["code"], unique=True)
    op.create_index(
        op.f("ix_risk_categories_sort_order"),
        "risk_categories",
        ["sort_order"],
        unique=False,
    )

    op.create_table(
        "asset_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asset_types")),
    )
    op.create_index(op.f("ix_asset_types_code"), "asset_types", ["code"], unique=True)

    op.create_table(
        "risk_subtypes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.SmallInteger(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.SmallInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["risk_categories.id"],
            name=op.f("fk_risk_subtypes_category_id_risk_categories"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_risk_subtypes")),
        sa.UniqueConstraint("category_id", "code", name=op.f("uq_risk_subtypes_category_id")),
    )
    op.create_index(
        op.f("ix_risk_subtypes_category_id"),
        "risk_subtypes",
        ["category_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_risk_subtypes_category_id"), table_name="risk_subtypes")
    op.drop_table("risk_subtypes")

    op.drop_index(op.f("ix_asset_types_code"), table_name="asset_types")
    op.drop_table("asset_types")

    op.drop_index(op.f("ix_risk_categories_sort_order"), table_name="risk_categories")
    op.drop_index(op.f("ix_risk_categories_code"), table_name="risk_categories")
    op.drop_table("risk_categories")

    op.drop_index(op.f("ix_attack_delivery_types_code"), table_name="attack_delivery_types")
    op.drop_table("attack_delivery_types")

    op.drop_index(op.f("ix_dataset_sources_code"), table_name="dataset_sources")
    op.drop_table("dataset_sources")
