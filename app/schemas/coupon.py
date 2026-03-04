import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CouponBase(BaseModel):
    """优惠券基础模型"""

    title: str = Field(..., max_length=128, description="优惠券标题")
    description: str | None = Field(None, max_length=256, description="备注/限领说明")
    discount_type: Literal["percent", "fixed"] = Field(
        ..., description="折扣类型: percent-百分比, fixed-固定金额"
    )
    discount_value: Decimal = Field(..., ge=0, description="折扣值")
    min_spend: Decimal = Field(
        Decimal("0.00"), ge=0, description="门槛金额 (满X元可用)"
    )
    total_quantity: int = Field(0, ge=0, description="发行总量 (0表示无限)")
    start_at: datetime = Field(..., description="有效期开始时间")
    end_at: datetime = Field(..., description="有效期结束时间")


class CouponCreateIn(CouponBase):
    """创建优惠券请求"""

    pass


class CouponUpdateIn(BaseModel):
    """更新优惠券请求"""

    title: str | None = Field(None, max_length=128)
    description: str | None = Field(None, max_length=256)
    discount_type: Literal["percent", "fixed"] | None = None
    discount_value: Decimal | None = Field(None, ge=0)
    min_spend: Decimal | None = Field(None, ge=0)
    total_quantity: int | None = Field(None, ge=0)
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: Literal["active", "inactive"] | None = None


class CouponOut(CouponBase):
    """优惠券详情响应"""

    id: uuid.UUID
    merchant_id: uuid.UUID | None = None
    issued_count: int
    status: str
    display_status: str | None = (
        None  # 动态计算的状态 (pending, active, expired, inactive)
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_display_status(self) -> "CouponOut":
        if self.status == "inactive":
            self.display_status = "inactive"
            return self

        compare_now = datetime.now(UTC) if self.start_at.tzinfo else datetime.now()

        if compare_now < self.start_at:
            self.display_status = "pending"
        elif compare_now > self.end_at:
            self.display_status = "expired"
        else:
            self.display_status = "active"
        return self


class UserCouponOut(BaseModel):
    """用户领取的优惠券详情"""

    id: uuid.UUID
    user_id: uuid.UUID
    coupon_id: uuid.UUID
    coupon: CouponOut | None = None  # 嵌入优惠券详情
    status: Literal["unused", "used", "expired"]
    used_at: datetime | None = None
    order_id: uuid.UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CouponClaimIn(BaseModel):
    """领取优惠券"""

    coupon_id: uuid.UUID


class CouponCenterOut(CouponOut):
    """领券中心的优惠券（附带当前用户的领取状态）"""

    is_claimed: bool = False
    is_fully_issued: bool = False


class AdminCouponListOut(BaseModel):
    """管理员：优惠券列表响应"""

    items: list[CouponOut]
    total: int
    page: int
    page_size: int
