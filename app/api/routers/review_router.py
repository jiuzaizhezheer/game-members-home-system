from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, status

from app.api.deps import get_current_user_id
from app.api.role import require_any_role, require_merchant
from app.schemas import SuccessResponse
from app.schemas.review import (
    ReviewCreateIn,
    ReviewListOut,
    ReviewOut,
    ReviewReplyIn,
)
from app.services.review_service import review_service

review_router = APIRouter()


@review_router.post(
    path="",
    dependencies=[require_any_role],
    response_model=SuccessResponse[ReviewOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_user_review(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[ReviewCreateIn, Body(description="评价内容")],
) -> SuccessResponse[ReviewOut]:
    """发表商品评价 (用户端)"""
    review = await review_service.create_review(user_id, payload)
    return SuccessResponse[ReviewOut](message="评价发表成功", data=review)


@review_router.get(
    path="/products/{product_id}",
    response_model=SuccessResponse[ReviewListOut],
    status_code=status.HTTP_200_OK,
)
async def get_product_reviews(
    product_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> SuccessResponse[ReviewListOut]:
    """获取某商品的评价列表 (公开接口)"""
    data = await review_service.get_product_reviews(product_id, page, page_size)
    return SuccessResponse[ReviewListOut](message="获取成功", data=data)


@review_router.get(
    path="/merchants",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ReviewListOut],
    status_code=status.HTTP_200_OK,
)
async def get_merchant_reviews(
    user_id: Annotated[str, Depends(get_current_user_id)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> SuccessResponse[ReviewListOut]:
    """获取商家收到的所有评价列表 (商家端)"""
    data = await review_service.get_merchant_reviews(user_id, page, page_size)
    return SuccessResponse[ReviewListOut](message="获取成功", data=data)


@review_router.post(
    path="/{review_id}/reply",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ReviewOut],
    status_code=status.HTTP_200_OK,
)
async def reply_review(
    user_id: Annotated[str, Depends(get_current_user_id)],
    review_id: str,
    payload: Annotated[ReviewReplyIn, Body(description="回复内容")],
) -> SuccessResponse[ReviewOut]:
    """商家回复评价 (商家端)"""
    review = await review_service.reply_review(user_id, review_id, payload)
    return SuccessResponse[ReviewOut](message="回复评价成功", data=review)
