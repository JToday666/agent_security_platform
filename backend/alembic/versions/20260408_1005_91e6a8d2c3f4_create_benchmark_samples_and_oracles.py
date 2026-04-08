"""create_benchmark_samples_and_oracles

Revision ID: 91e6a8d2c3f4
Revises: 50bfe4200b1a
Create Date: 2026-04-08 10:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "91e6a8d2c3f4"
down_revision: Union[str, Sequence[str], None] = "50bfe4200b1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "benchmark_samples",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("dataset_source_id", sa.SmallInteger(), nullable=False),
        sa.Column("sample_id", sa.Text(), nullable=False),
        sa.Column("sample_name", sa.Text(), nullable=True),
        sa.Column("resource_path", sa.Text(), nullable=False),
        sa.Column("entry_path", sa.Text(), nullable=False),
        sa.Column("user_goal", sa.Text(), nullable=False),
        sa.Column("attacker_goal", sa.Text(), nullable=True),
        sa.Column("attacker_is_user", sa.Boolean(), nullable=False),
        sa.Column("attack_delivery_type_id", sa.SmallInteger(), nullable=False),
        sa.Column("risk_subtype_id", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.SmallInteger(), nullable=False),
        sa.Column("attack_level", sa.SmallInteger(), nullable=False),
        sa.Column("difficulty_seed", sa.Numeric(4, 3), nullable=False),
        sa.Column("difficulty_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("difficulty_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asset_type_id", sa.Integer(), nullable=True),
        sa.Column("expected_safe_behavior", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("attack_level IN (1, 2, 3)", name=op.f("ck_benchmark_samples_attack_level_range")),
        sa.CheckConstraint(
            "difficulty_score >= 0 AND difficulty_score <= 1",
            name=op.f("ck_benchmark_samples_difficulty_score_range"),
        ),
        sa.CheckConstraint(
            "difficulty_seed >= 0 AND difficulty_seed <= 1",
            name=op.f("ck_benchmark_samples_difficulty_seed_range"),
        ),
        sa.CheckConstraint("risk_level IN (1, 2, 3)", name=op.f("ck_benchmark_samples_risk_level_range")),
        sa.ForeignKeyConstraint(
            ["asset_type_id"],
            ["asset_types.id"],
            name=op.f("fk_benchmark_samples_asset_type_id_asset_types"),
        ),
        sa.ForeignKeyConstraint(
            ["attack_delivery_type_id"],
            ["attack_delivery_types.id"],
            name=op.f("fk_benchmark_samples_attack_delivery_type_id_attack_delivery_types"),
        ),
        sa.ForeignKeyConstraint(
            ["dataset_source_id"],
            ["dataset_sources.id"],
            name=op.f("fk_benchmark_samples_dataset_source_id_dataset_sources"),
        ),
        sa.ForeignKeyConstraint(
            ["risk_subtype_id"],
            ["risk_subtypes.id"],
            name=op.f("fk_benchmark_samples_risk_subtype_id_risk_subtypes"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_benchmark_samples")),
        sa.UniqueConstraint("dataset_source_id", "sample_id", name=op.f("uq_benchmark_samples_dataset_source_id")),
    )
    op.create_index(
        op.f("ix_benchmark_samples_asset_type_id"),
        "benchmark_samples",
        ["asset_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_benchmark_samples_attack_delivery_type_id"),
        "benchmark_samples",
        ["attack_delivery_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_benchmark_samples_attack_level"),
        "benchmark_samples",
        ["attack_level"],
        unique=False,
    )
    op.create_index(
        op.f("ix_benchmark_samples_dataset_source_id"),
        "benchmark_samples",
        ["dataset_source_id"],
        unique=False,
    )
    op.create_index(
        "ix_benchmark_samples_dataset_source_id_is_active",
        "benchmark_samples",
        ["dataset_source_id", "is_active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_benchmark_samples_difficulty_score"),
        "benchmark_samples",
        ["difficulty_score"],
        unique=False,
    )
    op.create_index(
        op.f("ix_benchmark_samples_is_active"),
        "benchmark_samples",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_benchmark_samples_is_active_difficulty_score",
        "benchmark_samples",
        ["is_active", "difficulty_score"],
        unique=False,
    )
    op.create_index(
        op.f("ix_benchmark_samples_risk_level"),
        "benchmark_samples",
        ["risk_level"],
        unique=False,
    )
    op.create_index(
        op.f("ix_benchmark_samples_risk_subtype_id"),
        "benchmark_samples",
        ["risk_subtype_id"],
        unique=False,
    )
    op.create_index(
        "ix_benchmark_samples_risk_subtype_id_risk_level_attack_level",
        "benchmark_samples",
        ["risk_subtype_id", "risk_level", "attack_level"],
        unique=False,
    )

    op.create_table(
        "sample_oracles",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("sample_id_ref", sa.BigInteger(), nullable=False),
        sa.Column("oracle_kind", sa.SmallInteger(), nullable=False),
        sa.Column("seq_no", sa.SmallInteger(), nullable=False),
        sa.Column("display_text", sa.Text(), nullable=False),
        sa.Column("evaluator_type", sa.Text(), nullable=False),
        sa.Column("evaluator_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("oracle_kind IN (1, 2)", name=op.f("ck_sample_oracles_oracle_kind_range")),
        sa.ForeignKeyConstraint(
            ["sample_id_ref"],
            ["benchmark_samples.id"],
            name=op.f("fk_sample_oracles_sample_id_ref_benchmark_samples"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sample_oracles")),
        sa.UniqueConstraint(
            "sample_id_ref",
            "oracle_kind",
            "seq_no",
            name=op.f("uq_sample_oracles_sample_id_ref"),
        ),
    )
    op.create_index(
        op.f("ix_sample_oracles_sample_id_ref"),
        "sample_oracles",
        ["sample_id_ref"],
        unique=False,
    )
    op.create_index(
        "ix_sample_oracles_sample_id_ref_oracle_kind",
        "sample_oracles",
        ["sample_id_ref", "oracle_kind"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sample_oracles_sample_id_ref_oracle_kind", table_name="sample_oracles")
    op.drop_index(op.f("ix_sample_oracles_sample_id_ref"), table_name="sample_oracles")
    op.drop_table("sample_oracles")

    op.drop_index(
        "ix_benchmark_samples_risk_subtype_id_risk_level_attack_level",
        table_name="benchmark_samples",
    )
    op.drop_index(op.f("ix_benchmark_samples_risk_subtype_id"), table_name="benchmark_samples")
    op.drop_index(op.f("ix_benchmark_samples_risk_level"), table_name="benchmark_samples")
    op.drop_index(
        "ix_benchmark_samples_is_active_difficulty_score",
        table_name="benchmark_samples",
    )
    op.drop_index(op.f("ix_benchmark_samples_is_active"), table_name="benchmark_samples")
    op.drop_index(op.f("ix_benchmark_samples_difficulty_score"), table_name="benchmark_samples")
    op.drop_index("ix_benchmark_samples_dataset_source_id_is_active", table_name="benchmark_samples")
    op.drop_index(op.f("ix_benchmark_samples_dataset_source_id"), table_name="benchmark_samples")
    op.drop_index(op.f("ix_benchmark_samples_attack_level"), table_name="benchmark_samples")
    op.drop_index(
        op.f("ix_benchmark_samples_attack_delivery_type_id"),
        table_name="benchmark_samples",
    )
    op.drop_index(op.f("ix_benchmark_samples_asset_type_id"), table_name="benchmark_samples")
    op.drop_table("benchmark_samples")
