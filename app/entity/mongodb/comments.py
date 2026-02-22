from uuid import UUID

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.database.mongodb import BaseEntity


class CommentUserRedundancy(BaseModel):
    id: UUID = Field(..., description="用户ID")
    username: str = Field(..., description="用户昵称")
    avatar: str | None = Field(None, description="用户头像链接")


class Comment(BaseEntity):
    post_id: UUID = Field(..., description="关联的帖子 ID")
    user: CommentUserRedundancy = Field(..., description="冗余存储的用户信息")
    reply_to: CommentUserRedundancy | None = Field(None, description="被回复的用户信息")
    root_id: PydanticObjectId | None = Field(None, description="根评论 ID (顶层楼层)")
    parent_id: PydanticObjectId | None = Field(None, description="直接父评论 ID")
    content: str = Field(..., description="评论内容")
    likes_count: int = Field(default=0, description="点赞数")

    class Settings:
        name = "comments"
        indexes = [
            [("post_id", 1), ("root_id", 1), ("created_at", 1)],
            [("user.id", 1)],
        ]
