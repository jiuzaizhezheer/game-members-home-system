import uuid

from pydantic import BaseModel, ConfigDict, Field


class BannerBase(BaseModel):
    title: str = Field(..., max_length=128, description="标题")
    image_url: str = Field(..., max_length=512, description="图片链接")
    link_url: str | None = Field(None, max_length=512, description="跳转链接")
    sort_order: int = Field(0, description="排序权重")
    is_active: bool = Field(True, description="是否启用")


class BannerIn(BannerBase):
    """创建 Banner 的请求主体"""

    pass


class BannerUpdateIn(BaseModel):
    """更新 Banner 的请求主体 (全部可选)"""

    title: str | None = Field(None, max_length=128, description="标题")
    image_url: str | None = Field(None, max_length=512, description="图片链接")
    link_url: str | None = Field(None, max_length=512, description="跳转链接")
    sort_order: int | None = Field(None, description="排序权重")
    is_active: bool | None = Field(None, description="是否启用")


class BannerOut(BannerBase):
    """Banner 响应主体"""

    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class BannerListOut(BaseModel):
    """Banner 列表响应"""

    items: list[BannerOut]
    total: int
