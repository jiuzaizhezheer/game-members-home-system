import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Literal

import uuid6
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.pgsql import BaseEntity

if TYPE_CHECKING:
    from app.entity.pgsql.coupons import Coupon


class UserCoupon(BaseEntity):
    __tablename__ = "user_coupons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="用户优惠券关联ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="用户ID",
    )
    coupon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("coupons.id"),
        nullable=False,
        comment="优惠券ID",
    )

    # 建立与 Coupon 的关联
    coupon: Mapped["Coupon"] = relationship("Coupon")

    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        comment="使用的订单ID",
    )

    status: Mapped[Literal["unused", "used", "expired"]] = mapped_column(
        String(16),
        nullable=False,
        default="unused",
        comment="券状态: unused-未使用, used-已使用, expired-已过期",
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="核销时间"
    )

    __table_args__ = (
        Index("idx_user_coupons_user_status", "user_id", "status"),
        Index("idx_user_coupons_coupon", "coupon_id"),
        {"comment": "用户领取的优惠券清单"},
    )

    def __repr__(self) -> str:
        return f"UserCoupon(id={self.id}, user_id={self.user_id}, coupon_id={self.coupon_id}, status={self.status})"
