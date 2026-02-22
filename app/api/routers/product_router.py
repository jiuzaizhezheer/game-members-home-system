"""商品路由：商品资源 CRUD 接口"""

from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import get_current_user_id, get_product_service
from app.api.role import require_merchant
from app.common.constants import (
    GET_SUCCESS,
    PRODUCT_CREATE_SUCCESS,
    PRODUCT_DELETE_SUCCESS,
    PRODUCT_STATUS_UPDATE_SUCCESS,
    PRODUCT_UPDATE_SUCCESS,
)
from app.schemas import SuccessResponse
from app.schemas.product import (
    ProductCreateIn,
    ProductListOut,
    ProductOut,
    ProductPublicListOut,
    ProductPublicOut,
    ProductStatusIn,
    ProductUpdateIn,
)
from app.services import ProductService

product_router = APIRouter()


# ============ 公开接口 ============
@product_router.get(
    path="/",
    response_model=SuccessResponse[ProductPublicListOut],
    status_code=status.HTTP_200_OK,
)
async def get_public_products(
    product_service: Annotated[ProductService, Depends(get_product_service)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    keyword: Annotated[str | None, Query(description="搜索关键字")] = None,
    category_id: Annotated[str | None, Query(description="分类ID")] = None,
    sort_by: Annotated[
        Literal["price_asc", "price_desc", "newest", "popularity_desc"],
        Query(description="排序方式"),
    ] = "newest",
) -> SuccessResponse[ProductPublicListOut]:
    """获取公开商品列表"""
    products = await product_service.get_public_products(
        page=page,
        page_size=page_size,
        keyword=keyword,
        category_id=category_id,
        sort_by=sort_by,
    )
    return SuccessResponse[ProductPublicListOut](message=GET_SUCCESS, data=products)


@product_router.get(
    path="/{product_id}",
    response_model=SuccessResponse[ProductPublicOut],
    status_code=status.HTTP_200_OK,
)
async def get_public_product(
    product_id: Annotated[str, Path(description="商品ID")],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> SuccessResponse[ProductPublicOut]:
    """获取公开商品详情"""
    product = await product_service.get_product_public(product_id)
    return SuccessResponse[ProductPublicOut](message=GET_SUCCESS, data=product)


# ============ 商家操作（需要商家权限） ============
@product_router.get(
    path="/my/list",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ProductListOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_products(
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
    path="/my/{product_id}",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ProductOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_product(
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


@product_router.delete(
    path="/{product_id}",
    dependencies=[require_merchant],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def delete_product(
    user_id: Annotated[str, Depends(get_current_user_id)],
    product_id: Annotated[str, Path(description="商品ID")],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> SuccessResponse[None]:
    """删除商品"""
    await product_service.delete_product(user_id, product_id)
    return SuccessResponse[None](message=PRODUCT_DELETE_SUCCESS)
