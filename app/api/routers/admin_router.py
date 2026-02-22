"""
管理员路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    get_admin_service,
    get_current_user_id,
    get_user_service,
)
from app.api.role import require_admin
from app.common.constants import GET_SUCCESS
from app.schemas import SuccessResponse, UserOut
from app.schemas.admin import AdminDashboardOut
from app.services import AdminService, UserService

router = APIRouter()


@router.get(
    path="/profile",
    dependencies=[require_admin],
    response_model=SuccessResponse[UserOut],
    status_code=status.HTTP_200_OK,
)
async def get_admin_profile(
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    获取当前管理员信息
    """
    data = await user_service.get_profile(user_id)
    return SuccessResponse[UserOut](message=GET_SUCCESS, data=data)


@router.get(
    path="/dashboard",
    dependencies=[require_admin],
    response_model=SuccessResponse[AdminDashboardOut],
    status_code=status.HTTP_200_OK,
)
async def get_dashboard_stats(
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
):
    """
    获取管理后台仪表盘概览数据
    """
    data = await admin_service.get_dashboard_stats()
    return SuccessResponse[AdminDashboardOut](message=GET_SUCCESS, data=data)
