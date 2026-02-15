"""分类路由：分类资源接口"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_category_service
from app.common.constants import GET_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.category import CategoryOut
from app.services import CategoryService

category_router = APIRouter()


@category_router.get(
    path="/",
    response_model=SuccessResponse[list[CategoryOut]],
    status_code=status.HTTP_200_OK,
)
async def get_categories(
    category_service: Annotated[CategoryService, Depends(get_category_service)],
) -> SuccessResponse[list[CategoryOut]]:
    """获取分类列表（公开接口）"""
    categories = await category_service.get_all_categories()
    return SuccessResponse[list[CategoryOut]](message=GET_SUCCESS, data=categories)
