"""商家路由：商家店铺资源接口"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status

from app.api.deps import get_current_user_id, get_merchant_service
from app.api.role import require_merchant
from app.common.constants import GET_SUCCESS, MERCHANT_UPDATE_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.merchant import (
    MerchantOut,
    MerchantUpdateIn,
)
from app.services.merchant_service import MerchantService

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
