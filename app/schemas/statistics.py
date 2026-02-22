import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DashboardOverviewOut(BaseModel):
    """商家控制台数据概览"""

    total_sales: Decimal = Field(default=Decimal(0), description="总销售额")
    order_count: int = Field(default=0, description="订单数")
    product_count: int = Field(default=0, description="商品数")
    today_sales: Decimal = Field(default=Decimal(0), description="今日销售额")

    model_config = ConfigDict(from_attributes=True)


class SalesTrendItem(BaseModel):
    """销量趋势数据项"""

    date: str = Field(description="日期 (YYYY-MM-DD)")
    sales: Decimal = Field(default=Decimal(0), description="销售额")
    orders: int = Field(default=0, description="订单数")

    model_config = ConfigDict(from_attributes=True)


class SalesTrendOut(BaseModel):
    """销量趋势响应"""

    items: list[SalesTrendItem]

    model_config = ConfigDict(from_attributes=True)


class ProductRankingItem(BaseModel):
    """商品销量排行数据项"""

    product_id: uuid.UUID
    product_name: str
    image_url: str | None = None
    sales_amount: Decimal = Field(default=Decimal(0), description="销售额")
    sales_quantity: int = Field(default=0, description="销量(件数)")

    model_config = ConfigDict(from_attributes=True)


class ProductRankingOut(BaseModel):
    """商品销量排行响应"""

    items: list[ProductRankingItem]

    model_config = ConfigDict(from_attributes=True)
