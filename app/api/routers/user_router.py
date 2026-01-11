from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.api.deps import get_current_user_id, get_user_service
from app.api.role import require_member
from app.common.constants import CHANGE_PASSWORD_SUCCESS
from app.schemas import SuccessResponse, UserChangePasswordIn
from app.services import UserService
from app.utils import RateLimiter

user_router = APIRouter()


@user_router.put(
    path="/me/password",
    dependencies=[
        require_member,
        Depends(RateLimiter(counts=6, seconds=60)),
    ],  # TODO: 更多的角色
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
