from typing import Any
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.database.mongodb import BaseEntity


class AuditLog(BaseEntity):
    actor_id: UUID = Field(..., description="操作者 ID")
    action: str = Field(..., description="动作类型 (如 UPDATE_PRICE)")
    target_type: str = Field(..., description="目标类型 (如 product, order)")
    target_id: UUID = Field(..., description="目标 ID")
    detail: dict[str, Any] = Field(default_factory=dict, description="详细变更内容")
    ip: str = Field(..., description="操作者 IP 地址")

    class Settings:
        name = "audit_logs"
        indexes = [
            # 设置 TTL 索引，180 天自动过期
            IndexModel([("created_at", 1)], expireAfterSeconds=180 * 24 * 3600),
            [("actor_id", 1), ("created_at", -1)],
            [("target_id", 1)],
        ]
