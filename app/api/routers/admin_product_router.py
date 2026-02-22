"""
管理员 — 商品管理路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import get_admin_service, get_current_user_id
from app.api.role import require_admin
from app.common.constants import GET_SUCCESS, POST_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.product import ProductListOut, ProductOut
from app.services import AdminService

admin_product_router = APIRouter()


@admin_product_router.get(
    path="/",
    dependencies=[require_admin],
    response_model=SuccessResponse[ProductListOut],
    status_code=status.HTTP_200_OK,
)
async def get_product_list(
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    keyword: Annotated[str | None, Query(description="商品名搜索")] = None,
    product_status: Annotated[
        str | None, Query(alias="status", description="商品状态筛选")
    ] = None,
) -> SuccessResponse[ProductListOut]:
    """管理员查看全平台商品列表"""
    data = await admin_service.get_all_products(
        page=page, page_size=page_size, keyword=keyword, status=product_status
    )
    return SuccessResponse[ProductListOut](message=GET_SUCCESS, data=data)


@admin_product_router.get(
    path="/{id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[ProductOut],
    status_code=status.HTTP_200_OK,
)
async def get_product_detail(
    id: Annotated[str, Path(description="商品ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
) -> SuccessResponse[ProductOut]:
    """管理员查看商品详情"""
    data = await admin_service.get_product_detail(id)
    return SuccessResponse[ProductOut](message=GET_SUCCESS, data=data)


@admin_product_router.patch(
    path="/{id}/offline",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def force_offline_product(
    id: Annotated[str, Path(description="商品ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    admin_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[None]:
    """管理员强制下架商品"""
    await admin_service.force_offline_product(id, admin_id=admin_id)
    return SuccessResponse[None](message=POST_SUCCESS)
