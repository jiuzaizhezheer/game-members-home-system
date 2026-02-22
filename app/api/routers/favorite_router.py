"""收藏路由：收藏资源接口"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import get_current_user_id, get_favorite_service
from app.api.role import require_member
from app.common.constants import (
    FAVORITE_ADD_SUCCESS,
    FAVORITE_REMOVE_SUCCESS,
    GET_SUCCESS,
)
from app.schemas import SuccessResponse
from app.schemas.favorite import (
    FavoriteAddIn,
    FavoriteBatchDeleteIn,
    FavoriteCheckOut,
    FavoriteListOut,
)
from app.services.favorite_service import FavoriteService

favorite_router = APIRouter()


@favorite_router.get(
    path="/",
    dependencies=[require_member],
    response_model=SuccessResponse[FavoriteListOut],
    status_code=status.HTTP_200_OK,
)
async def get_favorites(
    user_id: Annotated[str, Depends(get_current_user_id)],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=50, description="每页数量")] = 20,
) -> SuccessResponse[FavoriteListOut]:
    """获取收藏列表"""
    data = await favorite_service.get_favorites(user_id, page=page, page_size=page_size)
    return SuccessResponse[FavoriteListOut](message=GET_SUCCESS, data=data)


@favorite_router.post(
    path="/",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_201_CREATED,
)
async def add_favorite(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[FavoriteAddIn, Body(description="添加收藏请求")],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
) -> SuccessResponse[None]:
    """添加收藏"""
    await favorite_service.add_favorite(user_id, str(payload.product_id))
    return SuccessResponse[None](message=FAVORITE_ADD_SUCCESS)


@favorite_router.get(
    path="/{product_id}/check",
    dependencies=[require_member],
    response_model=SuccessResponse[FavoriteCheckOut],
    status_code=status.HTTP_200_OK,
)
async def check_favorite(
    user_id: Annotated[str, Depends(get_current_user_id)],
    product_id: Annotated[str, Path(description="商品ID")],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
) -> SuccessResponse[FavoriteCheckOut]:
    """检查是否已收藏"""
    data = await favorite_service.check_favorited(user_id, product_id)
    return SuccessResponse[FavoriteCheckOut](message=GET_SUCCESS, data=data)


@favorite_router.delete(
    path="/batch",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def batch_remove_favorites(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[FavoriteBatchDeleteIn, Body(description="批量取消收藏请求")],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
) -> SuccessResponse[None]:
    """批量取消收藏"""
    await favorite_service.remove_batch(user_id, payload.product_ids)
    return SuccessResponse[None](message=FAVORITE_REMOVE_SUCCESS)


@favorite_router.delete(
    path="/{product_id}",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def remove_favorite(
    user_id: Annotated[str, Depends(get_current_user_id)],
    product_id: Annotated[str, Path(description="商品ID")],
    favorite_service: Annotated[FavoriteService, Depends(get_favorite_service)],
) -> SuccessResponse[None]:
    """取消收藏"""
    await favorite_service.remove_favorite(user_id, product_id)
    return SuccessResponse[None](message=FAVORITE_REMOVE_SUCCESS)
