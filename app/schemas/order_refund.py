import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class OrderRefundApplyIn(BaseModel):
    """用户申请退款请求数据"""

    reason: str = Field(min_length=1, max_length=255, description="退款原因")


class OrderRefundAuditIn(BaseModel):
    """商家审核退款请求数据"""

    status: Literal["approved", "rejected"] = Field(
        description="审核结果（approved/rejected）"
    )
    merchant_reply: str | None = Field(
        None, max_length=255, description="商家回复/备注"
    )


class OrderRefundOut(BaseModel):
    """退款记录响应数据"""

    id: uuid.UUID
    order_id: uuid.UUID
    user_id: uuid.UUID
    reason: str
    amount: Decimal
    status: str
    merchant_reply: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderRefundListOut(BaseModel):
    """退款列表响应"""

    items: list[OrderRefundOut]
    total: int
    page: int
    page_size: int
