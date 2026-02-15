from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.api.deps import get_current_user_id, get_user_service
from app.api.role import require_any_role
from app.common.constants import CHANGE_PASSWORD_SUCCESS, GET_SUCCESS
from app.schemas import (
    SuccessResponse,
    UserChangePasswordIn,
    UserOut,
    UserProfileUpdateIn,
)
from app.services import UserService
from app.utils import RateLimiter

user_router = APIRouter()


@user_router.get(
    path="/me",
    dependencies=[require_any_role],
    response_model=SuccessResponse[UserOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_profile(
    user_id: Annotated[str, Depends(get_current_user_id)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> SuccessResponse[UserOut]:
    """获取当前登录用户的个人资料"""
    user = await user_service.get_profile(user_id)
    return SuccessResponse[UserOut](message=GET_SUCCESS, data=user)


@user_router.put(
    path="/me",
    dependencies=[require_any_role],
    response_model=SuccessResponse[UserOut],
    status_code=status.HTTP_200_OK,
)
async def update_my_profile(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[UserProfileUpdateIn, Body(description="更新资料请求体")],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> SuccessResponse[UserOut]:
    """更新当前登录用户的个人资料"""
    user = await user_service.update_profile(user_id, payload)
    return SuccessResponse[UserOut](message="资料更新成功", data=user)


@user_router.put(
    path="/me/password",
    dependencies=[
        require_any_role,
        Depends(RateLimiter(counts=6, seconds=60)),
    ],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def change_password(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[UserChangePasswordIn, Body(description="修改密码请求体")],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> SuccessResponse[None]:
    """已登录情况下通过旧密码修改自己密码路由"""
    await user_service.change_password(user_id, payload)
    return SuccessResponse[None](message=CHANGE_PASSWORD_SUCCESS)


# TODO: 重置密码路由, 不需要验证旧密码与新密码是否相同
