import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import get_coupon_service
from app.api.role import require_admin
from app.common.constants import DELETE_SUCCESS, GET_SUCCESS, POST_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.coupon import (
    AdminCouponListOut,
    CouponCreateIn,
    CouponOut,
    CouponUpdateIn,
)
from app.services.coupon_service import CouponService

router = APIRouter()


@router.get(
    "",
    dependencies=[require_admin],
    response_model=SuccessResponse[AdminCouponListOut],
    status_code=status.HTTP_200_OK,
)
async def list_all_coupons(
    coupon_service: Annotated[CouponService, Depends(get_coupon_service)],
    merchant_id: Annotated[uuid.UUID | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """管理员：获取全量优惠券列表"""
    # 如果传了 merchant_id，则按商家过滤；否则查询全部（包含系统券）
    items, total = await coupon_service.list_merchant_coupons(
        merchant_id, page=page, page_size=page_size
    )
    data = AdminCouponListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
    return SuccessResponse[AdminCouponListOut](message=GET_SUCCESS, data=data)


@router.post(
    "",
    dependencies=[require_admin],
    response_model=SuccessResponse[CouponOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_platform_coupon(
    payload: Annotated[CouponCreateIn, Body()],
    coupon_service: Annotated[CouponService, Depends(get_coupon_service)],
):
    """管理员：创建平台通用优惠券 (merchant_id 为空)"""
    data = await coupon_service.create_coupon(None, payload)
    return SuccessResponse[CouponOut](message=POST_SUCCESS, data=data)


@router.put(
    "/{coupon_id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[CouponOut],
    status_code=status.HTTP_200_OK,
)
async def update_coupon(
    coupon_id: Annotated[uuid.UUID, Path()],
    payload: Annotated[CouponUpdateIn, Body()],
    coupon_service: Annotated[CouponService, Depends(get_coupon_service)],
):
    """管理员：更新任意优惠券信息"""
    data = await coupon_service.admin_update_coupon(coupon_id, payload)
    return SuccessResponse[CouponOut](message="更新成功", data=data)


@router.delete(
    "/{coupon_id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def delete_coupon(
    coupon_id: Annotated[uuid.UUID, Path()],
    coupon_service: Annotated[CouponService, Depends(get_coupon_service)],
):
    """管理员：删除/失效优惠券"""
    # 逻辑：将状态改为 inactive
    await coupon_service.admin_update_coupon(
        coupon_id, CouponUpdateIn.model_validate({"status": "inactive"})
    )
    return SuccessResponse[None](message=DELETE_SUCCESS, data=None)
