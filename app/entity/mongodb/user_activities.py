from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.database.mongodb import BaseEntity


class UserActivity(BaseEntity):
    user_id: UUID | None = Field(None, description="登录用户 ID (游客为 null)")
    session_id: str = Field(..., description="会话 ID (用于路径分析)")
    type: str = Field(
        ..., description="行为类型: view_product, search, add_to_cart, wishlist"
    )
    product_id: UUID | None = Field(None, description="关联商品 ID")
    keyword: str | None = Field(None, description="搜索关键词")
    platform: str = Field(default="pc", description="平台: pc, h5, app")

    class Settings:
        name = "user_activities"
        indexes = [
            # 设置 TTL 索引，90 天自动删除
            IndexModel([("created_at", 1)], expireAfterSeconds=90 * 24 * 3600),
            [("product_id", 1), ("type", 1)],
            [("user_id", 1), ("created_at", -1)],
        ]
