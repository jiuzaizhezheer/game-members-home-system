"""购物车相关的请求和响应模型"""

import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemAddIn(BaseModel):
    """验证添加商品到购物车"""

    product_id: uuid.UUID = Field(description="商品ID")
    quantity: int = Field(default=1, ge=1, le=99, description="购买数量")


class CartItemUpdateIn(BaseModel):
    """更新购物车商品数量"""

    quantity: int = Field(ge=1, le=99, description="购买数量")


class CartItemOut(BaseModel):
    """购物车明细响应"""

    id: uuid.UUID = Field(description="明细ID")
    product_id: uuid.UUID = Field(description="商品ID")
    product_name: str = Field(description="商品名称")
    product_image: str | None = Field(default=None, description="商品图片")
    unit_price: Decimal = Field(description="单价")
    quantity: int = Field(description="数量")
    subtotal: Decimal = Field(description="小计")

    model_config = {"from_attributes": True}


class CartCreateIn(BaseModel):
    """创建购物车请求"""

    name: str = Field(default="默认购物车", max_length=128, description="购物车名称")


class CartOut(BaseModel):
    """购物车完整响应"""

    id: uuid.UUID = Field(description="购物车ID")
    name: str = Field(description="购物车名称")
    is_checked_out: bool = Field(description="是否已结算")
    items: list[CartItemOut] = Field(default_factory=list, description="商品列表")
    total_amount: Decimal = Field(description="总金额")
    total_quantity: int = Field(description="商品总数")

    model_config = {"from_attributes": True}
