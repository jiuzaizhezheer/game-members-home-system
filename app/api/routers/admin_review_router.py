"""
管理员 — 评价管理路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import get_admin_service, get_current_user_id
from app.api.role import require_admin
from app.common.constants import GET_SUCCESS, POST_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.review import ReviewListOut
from app.services import AdminService

router = APIRouter()


@router.get(
    path="",
    dependencies=[require_admin],
    response_model=SuccessResponse[ReviewListOut],
    status_code=status.HTTP_200_OK,
)
async def get_all_reviews(
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    keyword: Annotated[str | None, Query(description="评价内容搜索")] = None,
) -> SuccessResponse[ReviewListOut]:
    """管理员查看全平台评价列表"""
    data = await admin_service.get_all_reviews(
        page=page, page_size=page_size, keyword=keyword
    )
    return SuccessResponse[ReviewListOut](message=GET_SUCCESS, data=data)


@router.delete(
    path="/{id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def delete_review(
    id: Annotated[str, Path(description="评价ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    admin_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[None]:
    """管理员删除评价"""
    await admin_service.delete_review(id, admin_id=admin_id)
    return SuccessResponse[None](message=POST_SUCCESS)
