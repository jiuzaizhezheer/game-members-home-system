from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.api.deps import get_captcha_service, get_current_user_id, get_user_service
from app.api.role import require_member
from app.common.constants import (
    CHANGE_PASSWORD_SUCCESS,
    INVALID_CAPTCHA,
    REGISTER_SUCCESS,
)
from app.common.errors import ValidationError
from app.model import (
    SuccessResponse,
    TokenOut,
    UserChangePasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services import CaptchaService, UserService
from app.utils.rate_limit import RateLimiter

user_router = APIRouter()


@user_router.post(
    path="/register",
    dependencies=[Depends(RateLimiter(counts=6, seconds=60))],  # TODO: 后续可能会预定义
    response_model=SuccessResponse[None],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: Annotated[UserRegisterRequest, Body(description="注册请求体")],
    user_service: Annotated[UserService, Depends(get_user_service)],
    captcha_service: Annotated[CaptchaService, Depends(get_captcha_service)],
) -> SuccessResponse[None]:
    """用户注册路由"""
    is_valid = await captcha_service.verify_captcha(
        payload.captcha_id,
        payload.captcha_code,
    )
    if not is_valid:
        raise ValidationError(INVALID_CAPTCHA)

    await user_service.register(payload)
    return SuccessResponse[None](message=REGISTER_SUCCESS)


@user_router.post(
    path="/login",
    dependencies=[Depends(RateLimiter(counts=6, seconds=60))],
    response_model=TokenOut,
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: Annotated[UserLoginRequest, Body(description="登录请求体")],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> TokenOut:
    """用户登录路由"""
    token_out = await user_service.login(payload)
    return token_out


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
    payload: Annotated[UserChangePasswordRequest, Body(description="修改密码请求体")],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> SuccessResponse[None]:
    """已登录情况下通过旧密码修改自己密码路由"""
    await user_service.change_password(user_id, payload)
    return SuccessResponse[None](message=CHANGE_PASSWORD_SUCCESS)


# TODO: 重置密码路由, 不需要验证旧密码与新密码是否相同
