"""商家路由：商家店铺资源接口"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import get_current_user_id, get_merchant_service, get_order_service
from app.api.role import require_merchant
from app.common.constants import (
    GET_SUCCESS,
    MERCHANT_UPDATE_SUCCESS,
    ORDER_SHIP_SUCCESS,
)
from app.schemas import SuccessResponse
from app.schemas.merchant import (
    MerchantOut,
    MerchantUpdateIn,
)
from app.schemas.order import OrderListOut
from app.services import MerchantService, OrderService

merchant_router = APIRouter()


@merchant_router.get(
    path="/my-merchant",
    dependencies=[require_merchant],
    response_model=SuccessResponse[MerchantOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_merchant(
    user_id: Annotated[str, Depends(get_current_user_id)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
) -> SuccessResponse[MerchantOut]:
    """获取当前商家信息"""
    merchant = await merchant_service.get_by_user_id(user_id)
    return SuccessResponse[MerchantOut](message=GET_SUCCESS, data=merchant)


@merchant_router.put(
    path="/{id}",
    dependencies=[require_merchant],
    response_model=SuccessResponse[MerchantOut],
    status_code=status.HTTP_200_OK,
)
async def update(
    id: Annotated[str, Path(description="商家ID")],
    payload: Annotated[MerchantUpdateIn, Body(description="商家信息更新请求")],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
) -> SuccessResponse[MerchantOut]:
    """更新商家信息"""
    merchant = await merchant_service.update(id, payload)
    return SuccessResponse[MerchantOut](message=MERCHANT_UPDATE_SUCCESS, data=merchant)


@merchant_router.get(
    path="/orders",
    dependencies=[require_merchant],
    response_model=SuccessResponse[OrderListOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_orders(
    user_id: Annotated[str, Depends(get_current_user_id)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    status: Annotated[str | None, Query(description="订单状态")] = None,
) -> SuccessResponse[OrderListOut]:
    """获取商家关联的订单列表"""
    items, total = await order_service.get_merchant_orders(
        user_id, page, page_size, status=status
    )
    return SuccessResponse[OrderListOut](
        message=GET_SUCCESS,
        data=OrderListOut(items=items, total=total, page=page, page_size=page_size),
    )


@merchant_router.post(
    path="/orders/{id}/ship",
    dependencies=[require_merchant],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def ship_order(
    id: Annotated[str, Path(description="订单ID")],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> SuccessResponse[None]:
    """订单发货"""
    await order_service.ship_order(id)
    return SuccessResponse[None](message=ORDER_SHIP_SUCCESS)
