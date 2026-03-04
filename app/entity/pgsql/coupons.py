import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

import uuid6
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class Coupon(BaseEntity):
    __tablename__ = "coupons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="优惠券ID",
    )
    merchant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="商家ID (为空表示平台券)",
    )
    title: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="优惠券标题"
    )
    description: Mapped[str | None] = mapped_column(String(256), comment="备注/说明")

    discount_type: Mapped[Literal["percent", "fixed"]] = mapped_column(
        String(16), nullable=False, comment="折扣类型: percent-百分比, fixed-固定金额"
    )
    discount_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="折扣值"
    )
    min_spend: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        server_default=text("0.00"),
        comment="最低消费金额门槛",
    )

    total_quantity: Mapped[int] = mapped_column(
        nullable=False, server_default=text("0"), comment="发行总量 (0表示无限)"
    )
    issued_count: Mapped[int] = mapped_column(
        nullable=False, server_default=text("0"), comment="已领数量"
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="有效开始时间"
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="有效结束时间"
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'active'"),
        comment="状态: active, inactive",
    )

    __table_args__ = (
        CheckConstraint("discount_value >= 0", name="chk_coupons_discount_value"),
        CheckConstraint("min_spend >= 0", name="chk_coupons_min_spend"),
        CheckConstraint("total_quantity >= 0", name="chk_coupons_total_quantity"),
        CheckConstraint("issued_count >= 0", name="chk_coupons_issued_count"),
        {"comment": "优惠券配置表"},
    )

    def __repr__(self) -> str:
        return f"Coupon(id={self.id}, title={self.title}, type={self.discount_type}, value={self.discount_value})"
