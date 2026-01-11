from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.api.deps import get_auth_service, get_captcha_service
from app.common.constants import (
    INVALID_CAPTCHA,
    LOGIN_SUCCESS,
    REGISTER_SUCCESS,
)
from app.common.errors import ValidationError
from app.schemas import AuthLoginIn, AuthRegisterIn, SuccessResponse, TokenOut
from app.services import AuthService, CaptchaService
from app.utils import RateLimiter

auth_router = APIRouter()


@auth_router.post(
    path="/register",
    dependencies=[Depends(RateLimiter(counts=6, seconds=60))],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: Annotated[AuthRegisterIn, Body(description="注册请求体")],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    captcha_service: Annotated[CaptchaService, Depends(get_captcha_service)],
) -> SuccessResponse[None]:
    """用户注册接口路由"""
    is_valid = await captcha_service.verify_captcha(
        payload.captcha_id,
        payload.captcha_code,
    )
    if not is_valid:
        raise ValidationError(INVALID_CAPTCHA)

    await auth_service.register(payload)
    return SuccessResponse[None](message=REGISTER_SUCCESS)


@auth_router.post(
    path="/login",
    dependencies=[Depends(RateLimiter(counts=6, seconds=60))],
    response_model=SuccessResponse[TokenOut],
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: Annotated[AuthLoginIn, Body(description="登录请求体")],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[TokenOut]:
    """用户登录接口路由"""
    token_out = await auth_service.login(payload)
    return SuccessResponse[TokenOut](message=LOGIN_SUCCESS, data=token_out)
