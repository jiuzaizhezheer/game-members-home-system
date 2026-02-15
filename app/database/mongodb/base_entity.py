from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field


class BaseEntity(Document):
    """
    MongoDB 基础实体类
    继承自 Beanie Document，增加了通用的时间戳字段
    """

    # 显式声明 id，Beanie 会自动将其映射为 MongoDB 的 _id
    id: PydanticObjectId | None = Field(None, description="MongoDB 自动生成的 ObjectId")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Settings:
        # 默认不限制集合，子类会覆盖
        pass

    async def update_timestamp(self):
        """更新时间戳的辅助方法"""
        self.updated_at = datetime.now()
        await self.save()
