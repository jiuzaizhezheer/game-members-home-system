from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewUserOut(BaseModel):
    id: UUID
    username: str
    avatar: str | None = None


# --- 请求体 ---
class ReviewCreateIn(BaseModel):
    order_id: str = Field(..., description="订单ID (必须已完成)")
    product_id: str = Field(..., description="要评价的商品ID")
    rating: int = Field(..., ge=1, le=5, description="评分 (1-5星)")
    content: str = Field(..., min_length=5, max_length=1000, description="评价文字内容")
    images: list[str] | None = Field(
        default=None, max_length=5, description="晒图 (最多5张)"
    )


class ReviewReplyIn(BaseModel):
    merchant_reply: str = Field(
        ..., min_length=2, max_length=1000, description="商家回复内容"
    )


# --- 响应体 ---
class ReviewOut(BaseModel):
    id: str = Field(..., description="评价记录的 MongoDB ObjectID")
    product_id: UUID
    order_id: UUID
    user: ReviewUserOut
    rating: int
    content: str
    images: list[str] = []
    merchant_reply: str | None = None
    reply_at: datetime | None = None
    product_name: str | None = None
    product_image: str | None = None
    created_at: datetime
    updated_at: datetime


class ReviewListOut(BaseModel):
    items: list[ReviewOut]
    total: int
    page: int
    page_size: int
