"""地址路由：地址资源 CRUD 接口"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from app.api.deps import get_address_service, get_current_user_id
from app.api.role import require_member
from app.common.constants import (
    GET_SUCCESS,
)
from app.schemas import SuccessResponse
from app.schemas.address import AddressCreateIn, AddressOut, AddressUpdateIn
from app.services.address_service import AddressService

address_router = APIRouter()


@address_router.get(
    path="/",
    dependencies=[require_member],
    response_model=SuccessResponse[list[AddressOut]],
    status_code=status.HTTP_200_OK,
)
async def get_my_addresses(
    user_id: Annotated[str, Depends(get_current_user_id)],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> SuccessResponse[list[AddressOut]]:
    """获取我的地址列表"""
    items = await address_service.get_my_addresses(user_id)
    return SuccessResponse[list[AddressOut]](message=GET_SUCCESS, data=items)


@address_router.post(
    path="/",
    dependencies=[require_member],
    response_model=SuccessResponse[AddressOut],
    status_code=status.HTTP_201_CREATED,
)
async def add_address(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[AddressCreateIn, Body(description="新增地址请求")],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> SuccessResponse[AddressOut]:
    """新增地址"""
    address = await address_service.add_address(user_id, payload)
    return SuccessResponse[AddressOut](message="添加成功", data=address)


@address_router.put(
    path="/{id}",
    dependencies=[require_member],
    response_model=SuccessResponse[AddressOut],
    status_code=status.HTTP_200_OK,
)
async def update_address(
    user_id: Annotated[str, Depends(get_current_user_id)],
    id: Annotated[str, Path(description="地址ID")],
    payload: Annotated[AddressUpdateIn, Body(description="更新地址请求")],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> SuccessResponse[AddressOut]:
    """更新地址"""
    address = await address_service.update_address(user_id, id, payload)
    return SuccessResponse[AddressOut](message="更新成功", data=address)


@address_router.delete(
    path="/{id}",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def delete_address(
    user_id: Annotated[str, Depends(get_current_user_id)],
    id: Annotated[str, Path(description="地址ID")],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> SuccessResponse[None]:
    """删除地址"""
    await address_service.delete_address(user_id, id)
    return SuccessResponse[None](message="删除成功")


@address_router.patch(
    path="/{id}/default",
    dependencies=[require_member],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def set_default(
    user_id: Annotated[str, Depends(get_current_user_id)],
    id: Annotated[str, Path(description="地址ID")],
    address_service: Annotated[AddressService, Depends(get_address_service)],
) -> SuccessResponse[None]:
    """设为默认地址"""
    await address_service.set_default(user_id, id)
    return SuccessResponse[None](message="设置默认成功")
