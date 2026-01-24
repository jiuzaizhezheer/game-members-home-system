"""商品路由：商品资源 CRUD 接口"""

from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import get_current_user_id, get_product_service
from app.api.role import require_merchant
from app.common.constants import (
    GET_SUCCESS,
    PRODUCT_CREATE_SUCCESS,
    PRODUCT_STATUS_UPDATE_SUCCESS,
    PRODUCT_UPDATE_SUCCESS,
)
from app.schemas import SuccessResponse
from app.schemas.product import (
    ProductCreateIn,
    ProductListOut,
    ProductOut,
    ProductStatusIn,
    ProductUpdateIn,
)
from app.services.product_service import ProductService

product_router = APIRouter()


# ============ 商家操作（需要商家权限） ============
@product_router.get(
    path="/",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ProductListOut],
    status_code=status.HTTP_200_OK,
)
async def get_products(
    user_id: Annotated[str, Depends(get_current_user_id)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 10,
    keyword: Annotated[str | None, Query(description="搜索关键字")] = None,
    status_filter: Annotated[
        Literal["on", "off"] | None, Query(alias="status", description="状态筛选")
    ] = None,
) -> SuccessResponse[ProductListOut]:
    """获取商家的商品列表"""
    products = await product_service.get_products_by_merchant(
        user_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status_filter,
    )
    return SuccessResponse[ProductListOut](message=GET_SUCCESS, data=products)


@product_router.get(
    path="/{product_id}",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ProductOut],
    status_code=status.HTTP_200_OK,
)
async def get_product(
    user_id: Annotated[str, Depends(get_current_user_id)],
    product_id: Annotated[str, Path(description="商品ID")],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> SuccessResponse[ProductOut]:
    """获取商品详情（商家）"""
    product = await product_service.get_product(user_id, product_id)
    return SuccessResponse[ProductOut](message=GET_SUCCESS, data=product)


@product_router.post(
    path="/",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ProductOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[ProductCreateIn, Body(description="创建商品请求")],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> SuccessResponse[ProductOut]:
    """创建商品"""
    product = await product_service.create_product(user_id, payload)
    return SuccessResponse[ProductOut](message=PRODUCT_CREATE_SUCCESS, data=product)


@product_router.put(
    path="/{product_id}",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ProductOut],
    status_code=status.HTTP_200_OK,
)
async def update_product(
    user_id: Annotated[str, Depends(get_current_user_id)],
    product_id: Annotated[str, Path(description="商品ID")],
    payload: Annotated[ProductUpdateIn, Body(description="更新商品请求")],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> SuccessResponse[ProductOut]:
    """更新商品"""
    product = await product_service.update_product(user_id, product_id, payload)
    return SuccessResponse[ProductOut](message=PRODUCT_UPDATE_SUCCESS, data=product)


@product_router.patch(
    path="/{product_id}/status",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ProductOut],
    status_code=status.HTTP_200_OK,
)
async def update_product_status(
    user_id: Annotated[str, Depends(get_current_user_id)],
    product_id: Annotated[str, Path(description="商品ID")],
    payload: Annotated[ProductStatusIn, Body(description="商品状态更新请求")],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> SuccessResponse[ProductOut]:
    """更新商品上下架状态"""
    product = await product_service.update_product_status(user_id, product_id, payload)
    return SuccessResponse[ProductOut](
        message=PRODUCT_STATUS_UPDATE_SUCCESS, data=product
    )
