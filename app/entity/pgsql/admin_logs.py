"""管理员操作日志实体"""

import uuid
from datetime import datetime

import uuid6
from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class AdminLog(BaseEntity):
    """管理员操作日志表"""

    __tablename__ = "admin_logs"
    __table_args__ = (
        Index("idx_admin_logs_admin_id", "admin_id"),
        Index("idx_admin_logs_created_at", "created_at"),
        {"comment": "管理员操作日志：记录所有管理端敏感操作"},
    )

    # admin_logs 表无 updated_at 列，覆盖 BaseEntity 继承的定义
    updated_at = None  # type: ignore[assignment]

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="日志ID",
    )
    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="操作管理员ID",
    )
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="操作类型，如 disable_user / verify_merchant / force_offline_product",
    )
    target_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="操作目标类型，如 user / merchant / product / post / comment",
    )
    target_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="操作目标ID（UUID字符串）",
    )
    detail: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="操作详情（JSON）",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="操作时间",
    )

    def __repr__(self) -> str:
        return f"AdminLog(id={self.id}, admin_id={self.admin_id}, action={self.action})"
