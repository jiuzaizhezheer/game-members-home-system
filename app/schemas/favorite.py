"""收藏相关的请求和响应模型"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class FavoriteAddIn(BaseModel):
    """添加收藏请求"""

    product_id: uuid.UUID = Field(description="商品ID")


class FavoriteBatchDeleteIn(BaseModel):
    """批量取消收藏请求"""

    product_ids: list[uuid.UUID] = Field(
        min_length=1, max_length=50, description="商品ID列表"
    )


class FavoriteItemOut(BaseModel):
    """收藏项响应"""

    product_id: uuid.UUID
    product_name: str
    product_image: str | None = None
    product_price: Decimal
    product_status: str
    created_at: datetime


class FavoriteListOut(BaseModel):
    """收藏列表响应"""

    items: list[FavoriteItemOut]
    total: int
    page: int
    page_size: int


class FavoriteCheckOut(BaseModel):
    """收藏状态响应"""

    is_favorited: bool
