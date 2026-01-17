"""分类相关的请求和响应模型"""

import uuid

from pydantic import BaseModel, Field


class CategoryOut(BaseModel):
    """分类响应"""

    id: uuid.UUID = Field(description="分类ID")
    name: str = Field(description="分类名称")
    slug: str = Field(description="分类别名")
    parent_id: uuid.UUID | None = Field(default=None, description="父分类ID")

    model_config = {"from_attributes": True}
