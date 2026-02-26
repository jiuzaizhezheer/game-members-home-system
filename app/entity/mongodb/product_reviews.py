from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.mongodb import BaseEntity


class ReviewUserRedundancy(BaseModel):
    id: UUID = Field(..., description="用户ID")
    username: str = Field(..., description="用户昵称")
    avatar: str | None = Field(None, description="用户头像链接")


class ProductReview(BaseEntity):
    product_id: UUID = Field(..., description="商品ID")
    order_id: UUID = Field(..., description="订单ID，用于防刷单和校验")
    user: ReviewUserRedundancy = Field(..., description="冗余的用户信息")
    rating: int = Field(..., ge=1, le=5, description="评分 (1-5)")
    content: str = Field(..., description="评价文字内容")
    images: list[str] = Field(default_factory=list, description="评价图片")
    merchant_reply: str | None = Field(None, description="商家回复内容")
    reply_at: datetime | None = Field(None, description="商家回复时间")

    class Settings:
        name = "product_reviews"
        indexes = [
            [("product_id", 1), ("created_at", -1)],
            [("order_id", 1), ("product_id", 1)],
            [("product_id", 1), ("rating", -1)],
        ]
