"""地址相关的请求和响应模型"""

import uuid

from pydantic import BaseModel, Field


class AddressCreateIn(BaseModel):
    """创建地址请求"""

    receiver_name: str = Field(min_length=2, max_length=64, description="收货人姓名")
    phone: str = Field(min_length=11, max_length=20, description="收货人手机号")
    province: str = Field(min_length=2, max_length=64, description="省份")
    city: str = Field(min_length=2, max_length=64, description="城市")
    district: str | None = Field(default=None, max_length=64, description="区县")
    detail: str = Field(min_length=5, max_length=255, description="详细地址")
    is_default: bool = Field(default=False, description="是否设置为默认地址")


class AddressUpdateIn(BaseModel):
    """更新地址请求"""

    receiver_name: str | None = Field(default=None, min_length=2, max_length=64)
    phone: str | None = Field(default=None, min_length=11, max_length=20)
    province: str | None = Field(default=None, min_length=2, max_length=64)
    city: str | None = Field(default=None, min_length=2, max_length=64)
    district: str | None = Field(default=None, max_length=64)
    detail: str | None = Field(default=None, min_length=5, max_length=255)
    is_default: bool | None = Field(default=None)


class AddressOut(BaseModel):
    """地址响应模型"""

    id: uuid.UUID
    user_id: uuid.UUID
    receiver_name: str
    phone: str
    province: str
    city: str
    district: str | None = None
    detail: str
    is_default: bool

    model_config = {"from_attributes": True}
