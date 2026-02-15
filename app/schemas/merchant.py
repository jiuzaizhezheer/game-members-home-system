"""商家相关的请求和响应模型"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MerchantOut(BaseModel):
    """商家信息响应"""

    id: uuid.UUID = Field(description="商家ID")
    user_id: uuid.UUID = Field(description="关联用户ID")
    shop_name: str = Field(description="店铺名称")
    contact_phone: str | None = Field(default=None, description="联系电话")
    shop_desc: str | None = Field(default=None, description="店铺描述")
    logo_url: str | None = Field(default=None, description="店铺Logo URL")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


class MerchantUpdateIn(BaseModel):
    """更新商家信息请求"""

    shop_name: str | None = Field(
        default=None, min_length=2, max_length=128, description="店铺名称"
    )
    contact_phone: str | None = Field(
        default=None, min_length=11, max_length=11, description="联系电话"
    )
    shop_desc: str | None = Field(default=None, description="店铺描述")
    logo_url: str | None = Field(default=None, description="店铺Logo URL")
