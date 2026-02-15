"""商品相关的请求和响应模型"""

import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ProductCreateIn(BaseModel):
    """创建商品请求"""

    name: str = Field(min_length=2, max_length=128, description="商品名称")
    sku: str | None = Field(default=None, max_length=64, description="商品SKU")
    description: str | None = Field(default=None, description="商品描述")
    price: Decimal = Field(ge=0, description="商品价格")
    stock: int = Field(default=0, ge=0, description="库存数量")
    category_ids: list[uuid.UUID] = Field(
        default_factory=list, description="分类ID列表"
    )
    image_url: str | None = Field(default=None, description="商品图片URL")

    @field_validator("sku", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        """将空字符串转换为 None，避免数据库唯一约束冲突"""
        if isinstance(v, str) and not v.strip():
            return None
        return v


class ProductUpdateIn(BaseModel):
    """更新商品请求"""

    name: str | None = Field(
        default=None, min_length=2, max_length=128, description="商品名称"
    )
    sku: str | None = Field(default=None, max_length=64, description="商品SKU")
    description: str | None = Field(default=None, description="商品描述")
    price: Decimal | None = Field(default=None, ge=0, description="商品价格")
    stock: int | None = Field(default=None, ge=0, description="库存数量")
    category_ids: list[uuid.UUID] | None = Field(default=None, description="分类ID列表")
    image_url: str | None = Field(default=None, description="商品图片URL")

    @field_validator("sku", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        """将空字符串转换为 None，避免数据库唯一约束冲突"""
        if isinstance(v, str) and not v.strip():
            return None
        return v


class ProductStatusIn(BaseModel):
    """商品上下架请求"""

    status: Literal["on", "off"] = Field(description="商品状态：on-上架，off-下架")


class ProductPublicOut(BaseModel):
    """公开商品响应（用户端）"""

    id: uuid.UUID = Field(description="商品ID")
    merchant_id: uuid.UUID = Field(description="商家ID")
    name: str = Field(description="商品名称")
    description: str | None = Field(default=None, description="商品描述")
    price: Decimal = Field(description="商品价格")
    stock: int = Field(description="库存数量")
    image_url: str | None = Field(default=None, description="商品图片URL")
    sales_count: int = Field(description="销售数量")

    category_ids: list[uuid.UUID] = Field(
        default_factory=list, description="分类ID列表"
    )

    model_config = {"from_attributes": True}


class ProductOut(ProductPublicOut):
    """商品完整响应（商家端）"""

    sku: str | None = Field(default=None, description="商品SKU")
    status: str = Field(description="商品状态")
    views_count: int = Field(description="浏览次数")

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    """商品列表响应"""

    items: list[ProductOut] = Field(description="商品列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页数量")


class ProductPublicListOut(BaseModel):
    """公开商品列表响应"""

    items: list[ProductPublicOut] = Field(description="商品列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页数量")
