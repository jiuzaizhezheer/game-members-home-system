"""购物车路由：购物车资源 CRUD 接口"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from app.api.deps import get_cart_service, get_current_user_id
from app.api.role import require_member
from app.common.constants import (
    CART_ADD_SUCCESS,
    CART_CLEAR_SUCCESS,
    CART_REMOVE_SUCCESS,
    CART_UPDATE_SUCCESS,
    GET_SUCCESS,
)
from app.schemas import SuccessResponse
from app.schemas.cart import CartCreateIn, CartItemAddIn, CartItemUpdateIn, CartOut
from app.services.cart_service import CartService

cart_router = APIRouter()


@cart_router.get(
    path="/list",
    dependencies=[require_member],
    response_model=SuccessResponse[list[CartOut]],
    status_code=status.HTTP_200_OK,
)
async def get_all_carts(
    user_id: Annotated[str, Depends(get_current_user_id)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> SuccessResponse[list[CartOut]]:
    """获取所有购物车列表"""
    carts = await cart_service.get_all_carts(user_id)
    return SuccessResponse[list[CartOut]](message=GET_SUCCESS, data=carts)


@cart_router.get(
    path="/",
    dependencies=[require_member],
    response_model=SuccessResponse[CartOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_cart(
    user_id: Annotated[str, Depends(get_current_user_id)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> SuccessResponse[CartOut]:
    """获取当前的活动购物车"""
    cart = await cart_service.get_my_cart(user_id)
    return SuccessResponse[CartOut](message=GET_SUCCESS, data=cart)


@cart_router.get(
    path="/{cart_id}",
    dependencies=[require_member],
    response_model=SuccessResponse[CartOut],
    status_code=status.HTTP_200_OK,
)
async def get_cart_detail(
    user_id: Annotated[str, Depends(get_current_user_id)],
    cart_id: Annotated[str, Path(description="购物车ID")],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> SuccessResponse[CartOut]:
    """获取特定购物车详情"""
    cart = await cart_service.get_my_cart(user_id, cart_id)
    return SuccessResponse[CartOut](message=GET_SUCCESS, data=cart)


@cart_router.post(
    path="/",
    dependencies=[require_member],
    response_model=SuccessResponse[CartOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_cart(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[CartCreateIn, Body(description="创建购物车请求")],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> SuccessResponse[CartOut]:
    """创建一个新的购物车"""
    cart = await cart_service.create_cart(user_id, payload.name)
    return SuccessResponse[CartOut](message="创建成功", data=cart)


@cart_router.post(
    path="/items",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_201_CREATED,
)
async def add_item(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[CartItemAddIn, Body(description="添加商品请求")],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> SuccessResponse[None]:
    """添加商品到当前活动购物车"""
    await cart_service.add_item(user_id, payload)
    return SuccessResponse[None](message=CART_ADD_SUCCESS)


@cart_router.put(
    path="/items/{item_id}",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def update_item(
    user_id: Annotated[str, Depends(get_current_user_id)],
    item_id: Annotated[str, Path(description="购物车明细ID")],
    payload: Annotated[CartItemUpdateIn, Body(description="更新数量请求")],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> SuccessResponse[None]:
    """更新当前活动购物车中的商品数量"""
    await cart_service.update_item(user_id, item_id, payload)
    return SuccessResponse[None](message=CART_UPDATE_SUCCESS)


@cart_router.delete(
    path="/items/{item_id}",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def remove_item(
    user_id: Annotated[str, Depends(get_current_user_id)],
    item_id: Annotated[str, Path(description="购物车明细ID")],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> SuccessResponse[None]:
    """从当前活动购物车移除商品"""
    await cart_service.remove_item(user_id, item_id)
    return SuccessResponse[None](message=CART_REMOVE_SUCCESS)


@cart_router.delete(
    path="/",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def clear_cart(
    user_id: Annotated[str, Depends(get_current_user_id)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
) -> SuccessResponse[None]:
    """清空当前活动购物车"""
    await cart_service.clear_cart(user_id)
    return SuccessResponse[None](message=CART_CLEAR_SUCCESS)
