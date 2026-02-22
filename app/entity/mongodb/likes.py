from uuid import UUID

from beanie import PydanticObjectId
from pydantic import Field

from app.database.mongodb import BaseEntity


class Like(BaseEntity):
    user_id: UUID = Field(..., description="点赞用户 ID")
    target_id: UUID | PydanticObjectId = Field(
        ..., description="目标对象 ID (Post UUID or Comment ObjectId)"
    )
    target_type: str = Field(..., description="目标类型: 'post' | 'comment'")

    class Settings:
        name = "likes"
        indexes = [
            [
                ("user_id", 1),
                ("target_id", 1),
                ("target_type", 1),
            ],  # 唯一索引确保不重复点赞
            [("target_id", 1), ("target_type", 1)],  # 查询某对象的点赞列表
        ]
