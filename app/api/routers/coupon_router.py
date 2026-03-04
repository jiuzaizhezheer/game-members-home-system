import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, status

from app.api.deps import get_coupon_service, get_current_user_id
from app.api.role import require_member
from app.common.constants import GET_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.coupon import CouponClaimIn, CouponOut, UserCouponOut
from app.services.coupon_service import CouponService

coupon_router = APIRouter()


@coupon_router.get(
    "/center",
    dependencies=[require_member],
    response_model=SuccessResponse[list[CouponOut]],
    status_code=status.HTTP_200_OK,
)
async def list_claimable_coupons(
    coupon_service: Annotated[CouponService, Depends(get_coupon_service)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """领券中心"""
    items, _ = await coupon_service.list_claimable_coupons(
        uuid.UUID(user_id), page, page_size
    )
    return SuccessResponse[list[CouponOut]](message=GET_SUCCESS, data=items)


@coupon_router.post(
    "/claim",
    dependencies=[require_member],
    response_model=SuccessResponse[UserCouponOut],
    status_code=status.HTTP_201_CREATED,
)
async def claim_coupon(
    payload: Annotated[CouponClaimIn, Body()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    coupon_service: Annotated[CouponService, Depends(get_coupon_service)],
):
    """领取优惠券"""
    data = await coupon_service.claim_coupon(uuid.UUID(user_id), payload.coupon_id)
    return SuccessResponse[UserCouponOut](message="领取成功", data=data)


@coupon_router.get(
    "/my",
    dependencies=[require_member],
    response_model=SuccessResponse[list[UserCouponOut]],
    status_code=status.HTTP_200_OK,
)
async def list_my_coupons(
    user_id: Annotated[str, Depends(get_current_user_id)],
    coupon_service: Annotated[CouponService, Depends(get_coupon_service)],
    status: str | None = Query(None, description="状态: unused, used, expired"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """我的券包"""
    items, _ = await coupon_service.list_my_coupons(
        uuid.UUID(user_id), status, page, page_size
    )
    return SuccessResponse[list[UserCouponOut]](message=GET_SUCCESS, data=items)
