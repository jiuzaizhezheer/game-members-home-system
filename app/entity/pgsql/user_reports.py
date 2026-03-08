import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class UserReport(BaseEntity):
    __tablename__ = "user_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="举报ID",
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="举报人ID",
    )
    target_type: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="目标类型: post/comment/product"
    )
    target_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="目标ID: UUID 或 Mongo ObjectId"
    )
    reason: Mapped[str] = mapped_column(String(64), nullable=False, comment="举报原因")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="补充说明"
    )
    evidence_urls: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=[],
        nullable=False,
        server_default=text("'{}'"),
        comment="证据图片URL列表",
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'pending'"),
        comment="状态: pending/handled",
    )
    result: Mapped[str | None] = mapped_column(
        String(16), nullable=True, comment="处理结果: success/fail"
    )
    handled_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="处理管理员ID",
    )
    handled_note: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="处理备注"
    )
    handled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="处理时间"
    )

    __table_args__ = (
        Index("idx_user_reports_status_created", "status", "created_at"),
        Index("idx_user_reports_target", "target_type", "target_id"),
        Index("idx_user_reports_reporter_created", "reporter_id", "created_at"),
        Index(
            "uq_user_reports_reporter_target_pending",
            "reporter_id",
            "target_type",
            "target_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        {"comment": "用户举报工单表"},
    )
