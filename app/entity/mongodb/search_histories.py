from uuid import UUID

from pydantic import Field

from app.database.mongodb import BaseEntity


class SearchHistory(BaseEntity):
    user_id: UUID = Field(..., description="用户 ID")
    keyword: str = Field(..., description="搜索关键词")
    frequency: int = Field(default=1, description="搜索频率")

    class Settings:
        name = "search_histories"
        indexes = [
            [("user_id", 1), ("updated_at", -1)],
            [("user_id", 1), ("keyword", 1)],  # 用于 upsert 时的快速定位
        ]
