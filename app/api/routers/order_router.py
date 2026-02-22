"""订单路由：订单资源接口"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import get_current_user_id, get_order_service
from app.api.role import require_member
from app.common.constants import (
    GET_SUCCESS,
    ORDER_CANCEL_SUCCESS,
    ORDER_PAY_SUCCESS,
    ORDER_RECEIPT_SUCCESS,
)
from app.schemas import SuccessResponse
from app.schemas.order import BuyNowIn, OrderCreateIn, OrderListOut, OrderOut
from app.services.order_service import OrderService

order_router = APIRouter()


@order_router.post(
    path="/",
    dependencies=[require_member],
    response_model=SuccessResponse[OrderOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[OrderCreateIn, Body(description="下单请求")],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> SuccessResponse[OrderOut]:
    """创建订单（从购物车结算）"""
    order = await order_service.create_from_cart(user_id, payload)
    return SuccessResponse[OrderOut](message="下单成功", data=order)


@order_router.post(
    path="/buy-now",
    dependencies=[require_member],
    response_model=SuccessResponse[OrderOut],
    status_code=status.HTTP_201_CREATED,
)
async def buy_now(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[BuyNowIn, Body(description="立即购买请求")],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> SuccessResponse[OrderOut]:
    """立即购买（绕过购物车直接下单）"""
    order = await order_service.buy_now(user_id, payload)
    return SuccessResponse[OrderOut](message="下单成功", data=order)


@order_router.get(
    path="/",
    dependencies=[require_member],
    response_model=SuccessResponse[OrderListOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_orders(
    user_id: Annotated[str, Depends(get_current_user_id)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> SuccessResponse[OrderListOut]:
    """批量获取我的订单"""
    items, total = await order_service.get_my_orders(user_id, page, page_size)
    return SuccessResponse[OrderListOut](
        message=GET_SUCCESS,
        data=OrderListOut(items=items, total=total, page=page, page_size=page_size),
    )


@order_router.get(
    path="/{id}",
    dependencies=[require_member],
    response_model=SuccessResponse[OrderOut],
    status_code=status.HTTP_200_OK,
)
async def get_order_detail(
    user_id: Annotated[str, Depends(get_current_user_id)],
    id: Annotated[str, Path(description="订单ID")],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> SuccessResponse[OrderOut]:
    """获取订单详情"""
    order = await order_service.get_order_detail(user_id, id)
    return SuccessResponse[OrderOut](message=GET_SUCCESS, data=order)


@order_router.post(
    path="/{id}/cancel",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def cancel_order(
    user_id: Annotated[str, Depends(get_current_user_id)],
    id: Annotated[str, Path(description="订单ID")],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> SuccessResponse[None]:
    """取消订单"""
    await order_service.cancel_order(user_id, id)
    return SuccessResponse[None](message=ORDER_CANCEL_SUCCESS)


@order_router.post(
    path="/{id}/pay",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def pay_order(
    user_id: Annotated[str, Depends(get_current_user_id)],
    id: Annotated[str, Path(description="订单ID")],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> SuccessResponse[None]:
    """模拟支付"""
    await order_service.pay_order(user_id, id)
    return SuccessResponse[None](message=ORDER_PAY_SUCCESS)


@order_router.post(
    path="/{id}/receipt",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def receipt_order(
    user_id: Annotated[str, Depends(get_current_user_id)],
    id: Annotated[str, Path(description="订单ID")],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> SuccessResponse[None]:
    """确认收货"""
    await order_service.receipt_order(user_id, id)
    return SuccessResponse[None](message=ORDER_RECEIPT_SUCCESS)
