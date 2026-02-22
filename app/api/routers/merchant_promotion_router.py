import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import (
    get_current_user_id,
    get_merchant_service,
    get_promotion_service,
)
from app.api.role import require_merchant
from app.common.constants import (
    GET_SUCCESS,
    POST_SUCCESS,
)
from app.common.errors import PermissionDeniedError
from app.schemas import SuccessResponse
from app.schemas.promotion import (
    PromotionCreateIn,
    PromotionDetailOut,
    PromotionListOut,
    PromotionOut,
    PromotionUpdateIn,
)
from app.services.merchant_service import MerchantService
from app.services.promotion_service import PromotionService

merchant_promotion_router = APIRouter()


@merchant_promotion_router.get(
    "",
    dependencies=[require_merchant],
    response_model=SuccessResponse[PromotionListOut],
    status_code=status.HTTP_200_OK,
)
async def list_promotions(
    user_id: Annotated[str, Depends(get_current_user_id)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
    promotion_service: Annotated[PromotionService, Depends(get_promotion_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取商家的促销活动列表"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    data = await promotion_service.list_promotions(merchant.id, page, page_size)
    return SuccessResponse[PromotionListOut](message=GET_SUCCESS, data=data)


@merchant_promotion_router.post(
    "",
    dependencies=[require_merchant],
    response_model=SuccessResponse[PromotionOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_promotion(
    payload: Annotated[PromotionCreateIn, Body()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
    promotion_service: Annotated[PromotionService, Depends(get_promotion_service)],
):
    """创建促销活动"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    data = await promotion_service.create_promotion(merchant.id, payload)
    return SuccessResponse[PromotionOut](message=POST_SUCCESS, data=data)


@merchant_promotion_router.get(
    "/{promotion_id}",
    dependencies=[require_merchant],
    response_model=SuccessResponse[PromotionDetailOut],
    status_code=status.HTTP_200_OK,
)
async def get_promotion(
    promotion_id: Annotated[uuid.UUID, Path()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
    promotion_service: Annotated[PromotionService, Depends(get_promotion_service)],
):
    """获取促销活动详情"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    data = await promotion_service.get_promotion(merchant.id, promotion_id)
    return SuccessResponse[PromotionDetailOut](message=GET_SUCCESS, data=data)


@merchant_promotion_router.put(
    "/{promotion_id}",
    dependencies=[require_merchant],
    response_model=SuccessResponse[PromotionOut],
    status_code=status.HTTP_200_OK,
)
async def update_promotion(
    promotion_id: Annotated[uuid.UUID, Path()],
    payload: Annotated[PromotionUpdateIn, Body()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
    promotion_service: Annotated[PromotionService, Depends(get_promotion_service)],
):
    """更新促销活动"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    data = await promotion_service.update_promotion(merchant.id, promotion_id, payload)
    return SuccessResponse[PromotionOut](message="Updated successfully", data=data)


@merchant_promotion_router.delete(
    "/{promotion_id}",
    dependencies=[require_merchant],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def delete_promotion(
    promotion_id: Annotated[uuid.UUID, Path()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
    promotion_service: Annotated[PromotionService, Depends(get_promotion_service)],
):
    """删除促销活动"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    await promotion_service.delete_promotion(merchant.id, promotion_id)
    return SuccessResponse[None](message="Deleted successfully")
