"""
管理员 — 商家管理路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import get_admin_service, get_current_user_id
from app.api.role import require_admin
from app.common.constants import GET_SUCCESS, POST_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.admin import AdminMerchantItemOut, AdminMerchantListOut
from app.services import AdminService

admin_merchant_router = APIRouter()


@admin_merchant_router.get(
    path="/",
    dependencies=[require_admin],
    response_model=SuccessResponse[AdminMerchantListOut],
    status_code=status.HTTP_200_OK,
)
async def get_merchant_list(
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    keyword: Annotated[str | None, Query(description="店铺名/用户名搜索")] = None,
) -> SuccessResponse[AdminMerchantListOut]:
    """管理员查看商家列表"""
    data = await admin_service.get_merchants(
        page=page, page_size=page_size, keyword=keyword
    )
    return SuccessResponse[AdminMerchantListOut](message=GET_SUCCESS, data=data)


@admin_merchant_router.get(
    path="/{id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[AdminMerchantItemOut],
    status_code=status.HTTP_200_OK,
)
async def get_merchant_detail(
    id: Annotated[str, Path(description="商家ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
) -> SuccessResponse[AdminMerchantItemOut]:
    """管理员查看商家详情"""
    data = await admin_service.get_merchant_detail(id)
    return SuccessResponse[AdminMerchantItemOut](message=GET_SUCCESS, data=data)


@admin_merchant_router.patch(
    path="/{id}/verify",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def verify_merchant(
    id: Annotated[str, Path(description="商家ID")],
    is_active: Annotated[bool, Query(description="审核结果：true=启用，false=禁用")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    admin_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[None]:
    """管理员审核商家（启用/禁用商家账号）"""
    await admin_service.verify_merchant(id, is_active, admin_id=admin_id)
    return SuccessResponse[None](message=POST_SUCCESS)
