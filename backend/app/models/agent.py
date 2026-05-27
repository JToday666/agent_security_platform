"""Agent registration ORM model."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base


class Agent(Base):
    """Persisted runnable Agent configuration owned by one user."""

    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_agents_public_id"),
        Index("ix_agents_user_id_status", "user_id", "status"),
        Index("ix_agents_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="Agent 主键 ID"
    )
    public_id: Mapped[str] = mapped_column(
        Text, nullable=False, comment="对外 Agent ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="创建用户 ID",
    )
    template_id: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="来源模板 ID"
    )
    name: Mapped[str] = mapped_column(Text, nullable=False, comment="Agent 名称")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Agent 描述"
    )
    invoke_mode: Mapped[str] = mapped_column(Text, nullable=False, comment="调用模式")
    max_concurrency: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4,
        server_default=text("4"),
        comment="该 Agent 允许同时运行的最大样本数",
    )
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'draft'"),
        index=True,
        comment="Agent 状态",
    )
    connection: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, comment="连接配置"
    )
    auth_type: Mapped[str] = mapped_column(Text, nullable=False, comment="鉴权类型")
    auth_public_config: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, comment="非敏感鉴权配置"
    )
    credential_ref: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="凭据引用"
    )
    platform_input_mapping: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, comment="平台输入字段映射"
    )
    task_render_mode: Mapped[str] = mapped_column(
        Text, nullable=False, comment="任务渲染模式"
    )
    custom_request_body: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, comment="固定请求体字段"
    )
    request_options: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, comment="请求选项"
    )
    platform_output_mapping: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, comment="响应字段映射"
    )
    terminal_statuses: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, comment="外部终态集合"
    )
    success_statuses: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, comment="外部成功态集合"
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最近验证时间"
    )
    last_verification_passed: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, comment="最近验证是否通过"
    )
    last_verification: Mapped[dict[str, object] | None] = mapped_column(
        JSONB, nullable=True, comment="最近验证结果"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
