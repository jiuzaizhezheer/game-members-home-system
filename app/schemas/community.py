import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Group ---
class GroupItemOut(BaseModel):
    id: uuid.UUID
    name: str = Field(description="社群名称")
    description: str | None = Field(None, description="描述")
    cover_image: str | None = Field(None, description="封面图")
    member_count: int = Field(0, description="成员数")
    post_count: int = Field(0, description="帖子数")
    is_joined: bool = Field(False, description="是否已加入")
    merchant_id: uuid.UUID | None = Field(None, description="所属商家ID")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupListOut(BaseModel):
    items: list[GroupItemOut]
    total: int


class GroupDetailOut(GroupItemOut):
    pass


class GroupCreateIn(BaseModel):
    name: str = Field(..., max_length=128)
    description: str | None = None
    cover_image: str | None = None
    merchant_id: uuid.UUID | None = None  # Internal use or admin override


class GroupUpdateIn(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    cover_image: str | None = None


# --- Post ---
class PostCreateIn(BaseModel):
    group_id: uuid.UUID
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=2)
    images: list[str] = Field(default=[], max_length=9)
    videos: list[str] = Field(default=[], max_length=1)


class PostUpdateIn(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=255)
    content: str | None = Field(None, min_length=2)
    images: list[str] | None = Field(None, max_length=9)
    videos: list[str] | None = Field(None, max_length=1)


class PostItemOut(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    group_name: str
    author_id: uuid.UUID
    author_name: str
    author_avatar: str | None = None
    title: str
    content: str
    images: list[str] = []
    videos: list[str] = []
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    is_liked: bool = False
    is_mine: bool = False
    is_top: bool = False
    is_hidden: bool = False  # Added for moderation
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostListOut(BaseModel):
    items: list[PostItemOut]
    total: int
    page: int
    page_size: int


class PostDetailOut(PostItemOut):
    pass


# --- Comment ---
class CommentCreateIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: str | None = None


class CommentItemOut(BaseModel):
    id: str
    post_id: uuid.UUID
    author_id: uuid.UUID
    author_name: str
    author_avatar: str | None = None
    content: str
    parent_id: str | None = None
    reply_to_username: str | None = None
    like_count: int = 0
    is_liked: bool = False
    reply_count: int = 0
    created_at: datetime
    replies: list["CommentItemOut"] = []

    model_config = ConfigDict(from_attributes=True)


class CommentListOut(BaseModel):
    items: list[CommentItemOut]
    total: int
    page: int
    page_size: int


# --- Like ---
class LikeToggleIn(BaseModel):
    target_id: str
    target_type: str = Field(..., pattern="^(post|comment)$")
