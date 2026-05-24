"""Worker process observability models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base


class WorkerProcess(Base):
    """Tracks scheduler and sample worker process heartbeat state."""

    __tablename__ = "worker_processes"
    __table_args__ = (
        Index("ix_worker_processes_role_status", "role", "status"),
        Index("ix_worker_processes_last_heartbeat_at", "last_heartbeat_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    worker_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    hostname: Mapped[str] = mapped_column(Text, nullable=False)
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="starting", server_default=text("'starting'")
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    active_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    process_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
