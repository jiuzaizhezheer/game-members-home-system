"""分类相关的请求和响应模型"""

import uuid

from pydantic import BaseModel, Field


class CategoryCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=64, description="分类名称")
    slug: str = Field(min_length=1, max_length=64, description="分类别名")


class CategoryUpdateIn(BaseModel):
    name: str | None = Field(
        default=None, min_length=1, max_length=64, description="分类名称"
    )
    slug: str | None = Field(
        default=None, min_length=1, max_length=64, description="分类别名"
    )


class CategoryOut(BaseModel):
    """分类响应"""

    id: uuid.UUID = Field(description="分类ID")
    name: str = Field(description="分类名称")
    slug: str = Field(description="分类别名")

    model_config = {"from_attributes": True}
