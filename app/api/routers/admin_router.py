"""
管理员路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_community_service, get_current_user_id, get_user_service
from app.api.role import require_admin
from app.common.constants import GET_SUCCESS, POST_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.community import GroupCreateIn, GroupDetailOut
from app.services import CommunityService, UserService

router = APIRouter(dependencies=[require_admin])


@router.get("/profile")
async def get_admin_profile(
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    获取当前管理员信息
    """
    user = await user_service.get_by_id(user_id)
    return SuccessResponse(
        message=GET_SUCCESS,
        data={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    )


@router.get("/dashboard")
async def get_dashboard_stats():
    """
    获取管理后台仪表盘概览数据（占位）
    """
    # TODO: 后续扩展，添加真实的统计数据
    return SuccessResponse(
        message=GET_SUCCESS,
        data={
            "total_users": 0,
            "total_merchants": 0,
            "total_products": 0,
            "total_orders": 0,
            "pending_audits": 0,
        },
    )


# --- Community Management ---


@router.post(
    "/community/groups", response_model=SuccessResponse[GroupDetailOut], status_code=201
)
async def create_community_group(
    payload: GroupCreateIn,
    service: Annotated[CommunityService, Depends(get_community_service)],
):
    """
    管理员创建话题圈
    """
    data = await service.create_group(payload)
    return SuccessResponse[GroupDetailOut](message=POST_SUCCESS, data=data)
