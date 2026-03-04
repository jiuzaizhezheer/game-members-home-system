import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LogisticsBase(BaseModel):
    status_message: str = Field(..., max_length=256, description="状态描述")
    location: str | None = Field(None, max_length=128, description="地理位置")
    log_time: datetime = Field(default_factory=datetime.now, description="记录时间")


class LogisticsOut(LogisticsBase):
    """物流追踪项响应主体"""

    id: uuid.UUID
    order_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class OrderLogisticsOut(BaseModel):
    """整个订单的物流追踪图谱"""

    order_id: uuid.UUID
    tracking_no: str | None = None
    courier_name: str | None = None
    items: list[LogisticsOut]
