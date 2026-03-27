from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DatasetSource(Base):
    __tablename__ = "dataset_sources"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AttackDeliveryType(Base):
    __tablename__ = "attack_delivery_types"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RiskCategory(Base):
    __tablename__ = "risk_categories"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RiskSubtype(Base):
    __tablename__ = "risk_subtypes"
    __table_args__ = (
        UniqueConstraint("category_id", "code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("risk_categories.id"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AssetType(Base):
    __tablename__ = "asset_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BenchmarkSample(Base):
    __tablename__ = "benchmark_samples"
    __table_args__ = (
        UniqueConstraint("dataset_source_id", "sample_id"),
        CheckConstraint("risk_level IN (1, 2, 3)", name="risk_level_range"),
        CheckConstraint("attack_level IN (1, 2, 3)", name="attack_level_range"),
        Index(
            "ix_benchmark_samples_risk_subtype_id_risk_level_attack_level",
            "risk_subtype_id",
            "risk_level",
            "attack_level",
        ),
        Index(
            "ix_benchmark_samples_dataset_source_id_is_active",
            "dataset_source_id",
            "is_active",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dataset_source_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("dataset_sources.id"),
        nullable=False,
        index=True,
    )
    sample_id: Mapped[str] = mapped_column(Text, nullable=False)
    sample_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_path: Mapped[str] = mapped_column(Text, nullable=False)
    entry_path: Mapped[str] = mapped_column(Text, nullable=False)
    user_goal: Mapped[str] = mapped_column(Text, nullable=False)
    attacker_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    attacker_is_user: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attack_delivery_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("attack_delivery_types.id"),
        nullable=False,
        index=True,
    )
    risk_subtype_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("risk_subtypes.id"),
        nullable=False,
        index=True,
    )
    risk_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True)
    attack_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True)
    asset_type_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("asset_types.id"),
        nullable=True,
        index=True,
    )
    expected_safe_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SampleOracle(Base):
    __tablename__ = "sample_oracles"
    __table_args__ = (
        UniqueConstraint("sample_id_ref", "oracle_kind", "seq_no"),
        CheckConstraint("oracle_kind IN (1, 2)", name="oracle_kind_range"),
        Index(
            "ix_sample_oracles_sample_id_ref_oracle_kind",
            "sample_id_ref",
            "oracle_kind",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sample_id_ref: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("benchmark_samples.id"),
        nullable=False,
        index=True,
    )
    oracle_kind: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    seq_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    display_text: Mapped[str] = mapped_column(Text, nullable=False)
    evaluator_type: Mapped[str] = mapped_column(Text, nullable=False)
    evaluator_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )
