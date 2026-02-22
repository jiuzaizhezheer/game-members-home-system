"""
管理员 — 用户管理路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import get_admin_service, get_current_user_id
from app.api.role import require_admin
from app.common.constants import GET_SUCCESS, POST_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.admin import AdminUserItemOut, AdminUserListOut
from app.services import AdminService

admin_user_router = APIRouter()


@admin_user_router.get(
    path="/",
    dependencies=[require_admin],
    response_model=SuccessResponse[AdminUserListOut],
    status_code=status.HTTP_200_OK,
)
async def get_user_list(
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    keyword: Annotated[str | None, Query(description="用户名/邮箱搜索")] = None,
    role: Annotated[str | None, Query(description="角色筛选")] = None,
    is_active: Annotated[bool | None, Query(description="激活状态筛选")] = None,
) -> SuccessResponse[AdminUserListOut]:
    """管理员查看用户列表"""
    data = await admin_service.get_users(
        page=page,
        page_size=page_size,
        keyword=keyword,
        role=role,
        is_active=is_active,
    )
    return SuccessResponse[AdminUserListOut](message=GET_SUCCESS, data=data)


@admin_user_router.get(
    path="/{id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[AdminUserItemOut],
    status_code=status.HTTP_200_OK,
)
async def get_user_detail(
    id: Annotated[str, Path(description="用户ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
) -> SuccessResponse[AdminUserItemOut]:
    """管理员查看用户详情"""
    data = await admin_service.get_user_detail(id)
    return SuccessResponse[AdminUserItemOut](message=GET_SUCCESS, data=data)


@admin_user_router.patch(
    path="/{id}/disable",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def disable_user(
    id: Annotated[str, Path(description="用户ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    admin_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[None]:
    """管理员禁用用户"""
    await admin_service.disable_user(id, admin_id=admin_id)
    return SuccessResponse[None](message=POST_SUCCESS)


@admin_user_router.patch(
    path="/{id}/enable",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def enable_user(
    id: Annotated[str, Path(description="用户ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    admin_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[None]:
    """管理员启用用户"""
    await admin_service.enable_user(id, admin_id=admin_id)
    return SuccessResponse[None](message=POST_SUCCESS)
