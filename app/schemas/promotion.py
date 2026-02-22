import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.product import ProductPublicOut


class PromotionBase(BaseModel):
    """促销活动基础模型"""

    title: str = Field(min_length=2, max_length=128, description="活动标题")
    discount_type: Literal["percent", "fixed"] = Field(
        description="优惠类型: percent-百分比, fixed-固定金额"
    )
    discount_value: Decimal = Field(ge=0, description="优惠值")
    start_at: datetime = Field(description="开始时间")
    end_at: datetime = Field(description="结束时间")
    status: Literal["active", "inactive"] = Field(
        default="active", description="活动状态"
    )

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                pass
        return v

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValueError("结束时间必须晚于开始时间")
        return self

    @model_validator(mode="after")
    def check_discount_value(self):
        if self.discount_type == "percent" and self.discount_value > 100:
            raise ValueError("百分比折扣不能超过100")
        return self


class PromotionCreateIn(PromotionBase):
    """创建促销活动请求"""

    product_ids: list[uuid.UUID] = Field(description="参与活动的商品ID列表")


class PromotionUpdateIn(BaseModel):
    """更新促销活动请求"""

    title: str | None = Field(None, min_length=2, max_length=128)
    discount_type: Literal["percent", "fixed"] | None = None
    discount_value: Decimal | None = Field(None, ge=0)
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: Literal["active", "inactive"] | None = None
    product_ids: list[uuid.UUID] | None = None

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                pass
        return v


class PromotionOut(PromotionBase):
    """促销活动响应"""

    id: uuid.UUID
    merchant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromotionSimpleOut(BaseModel):
    """简化的促销活动信息（用于嵌入商品响应）"""

    id: uuid.UUID
    title: str
    discount_type: Literal["percent", "fixed"]
    discount_value: Decimal
    start_at: datetime
    end_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromotionDetailOut(PromotionOut):
    """促销活动详情响应（包含商品）"""

    products: list[ProductPublicOut] = Field(
        default_factory=list, description="参与商品"
    )


class PromotionListOut(BaseModel):
    """促销活动列表响应"""

    items: list[PromotionOut]
    total: int
    page: int
    page_size: int
