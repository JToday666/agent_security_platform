"""用户模型定义，负责映射账号、权限与审计字段。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base


class User(Base):
    """定义用户表结构，供认证、资料管理等模块共享使用。"""

    __tablename__ = "users"

    # 主键 ID
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="用户ID")

    # 账号基本信息
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="用户名(唯一)"
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, comment="电子邮箱(唯一)"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="加密后的密码"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="用户头像URL"
    )

    # 状态与权限
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="是否激活",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="是否为超级管理员",
    )

    # 审计时间字段
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
        comment="最后更新时间",
    )
