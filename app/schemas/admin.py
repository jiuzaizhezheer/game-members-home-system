"""管理员模块 Schema"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import RoleEnum


class AdminDashboardOut(BaseModel):
    """管理员仪表盘统计数据"""

    total_users: int
    total_merchants: int
    total_products: int
    total_orders: int
    pending_audits: int


# --- 用户管理 ---


class AdminUserItemOut(BaseModel):
    """管理端用户列表项"""

    id: uuid.UUID = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: EmailStr = Field(description="邮箱")
    role: RoleEnum = Field(description="角色")
    is_active: bool = Field(description="是否激活")
    avatar_url: str | None = Field(default=None, description="头像地址")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


class AdminUserListOut(BaseModel):
    """管理端用户列表响应"""

    items: list[AdminUserItemOut] = Field(description="用户列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页数量")


# --- 操作日志 ---


class AdminLogItemOut(BaseModel):
    """管理员操作日志单条"""

    id: uuid.UUID = Field(description="日志ID")
    admin_id: uuid.UUID = Field(description="管理员ID")
    action: str = Field(description="操作类型")
    target_type: str = Field(description="目标类型")
    target_id: str = Field(description="目标ID")
    detail: dict | None = Field(default=None, description="详情")
    created_at: datetime = Field(description="操作时间")

    model_config = {"from_attributes": True}


class AdminLogListOut(BaseModel):
    """管理员操作日志列表响应"""

    items: list[AdminLogItemOut] = Field(description="日志列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页数量")
