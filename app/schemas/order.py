"""订单相关的请求和响应模型"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.address import AddressOut


class OrderCreateIn(BaseModel):
    """创建订单请求"""

    address_id: uuid.UUID = Field(description="收货地址ID")


class BuyNowIn(BaseModel):
    """立即购买请求（绕过购物车）"""

    product_id: uuid.UUID = Field(description="商品ID")
    quantity: int = Field(ge=1, description="购买数量")
    address_id: uuid.UUID = Field(description="收货地址ID")


class OrderShipIn(BaseModel):
    """商家发货请求数据"""

    courier_name: str = Field(min_length=1, max_length=64, description="快递公司名称")
    tracking_no: str = Field(min_length=1, max_length=64, description="物流单号")


class OrderItemOut(BaseModel):
    """订单明细响应"""

    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str = Field(
        description="冗余商品名称，展示用"
    )  # 实际可能需查 Product 或在 Repo Join
    quantity: int
    unit_price: Decimal
    product_image: str | None = Field(None, description="商品图片URL")

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    """订单响应模型"""

    id: uuid.UUID
    order_no: str
    status: str
    total_amount: Decimal
    address_id: uuid.UUID | None
    address: AddressOut | None = None
    created_at: datetime
    courier_name: str | None = None
    tracking_no: str | None = None
    items: list[OrderItemOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class OrderListOut(BaseModel):
    """订单列表响应"""

    items: list[OrderOut]
    total: int
    page: int
    page_size: int
