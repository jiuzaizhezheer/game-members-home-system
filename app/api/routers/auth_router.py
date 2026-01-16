from typing import Annotated

from fastapi import APIRouter, Body, Cookie, Depends, Response, status, HTTPException

from app.api.deps import get_auth_service, get_captcha_service
from app.common.constants import (
    INVALID_CAPTCHA,
    LOGIN_SUCCESS,
    REFRESH_TOKEN_SUCCESS,
    REGISTER_SUCCESS,
)
from app.common.errors import ValidationError
from app.schemas import (
    AccessTokenOut,
    AuthLoginIn,
    AuthRegisterIn,
    SuccessResponse,
)
from app.services import AuthService, CaptchaService
from app.utils import RateLimiter
from app.core.config import ENV, REFRESH_TOKEN_EXPIRE_DAYS
from app.utils import delete_refresh_token

auth_router = APIRouter()
REFRESH_PATH="/api/auths/refresh"


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_CAPTCHA,
        )

    await auth_service.register(payload)
    return SuccessResponse[None](message=REGISTER_SUCCESS)


@auth_router.post(
    path="/login",
    dependencies=[Depends(RateLimiter(counts=6, seconds=60))],
    response_model=SuccessResponse[AccessTokenOut],
    status_code=status.HTTP_200_OK,
)
async def login(
    response: Response,
    payload: Annotated[AuthLoginIn, Body(description="登录请求体")],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[AccessTokenOut]:
    """用户登录接口路由"""
    token_out = await auth_service.login(payload)

    # 设置 HttpOnly Cookie
    response.set_cookie(
        key="refresh_token",
        value=token_out.refresh_token,
        httponly=True,
        secure=ENV == "production", # TODO 开发环境如果不使用 HTTPS 可以先注释，生产环境必须开启为true
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 7 天
        path=REFRESH_PATH,
    )

    return SuccessResponse[AccessTokenOut](
        message=LOGIN_SUCCESS,
        data=AccessTokenOut(access_token=token_out.access_token),
    )


@auth_router.post(
    path="/refresh",
    dependencies=[Depends(RateLimiter(counts=10, seconds=60))],
    response_model=SuccessResponse[AccessTokenOut],
    status_code=status.HTTP_200_OK,
)
async def refresh_all_token(
    response: Response,
    refresh_token: Annotated[str, Cookie(description="刷新令牌")],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[AccessTokenOut]:
    """
    刷新令牌接口路由
    从 Cookie 中获取 refresh_token，返回新的 access_token
    """
    try:
        token_out = await auth_service.refresh_all_token(refresh_token)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
    # 刷新 Cookie
    response.set_cookie(
        key="refresh_token",
        value=token_out.refresh_token,
        httponly=True,
        secure=ENV == "production",
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=REFRESH_PATH,
    )

    return SuccessResponse[AccessTokenOut](
        message=REFRESH_TOKEN_SUCCESS,
        data=AccessTokenOut(access_token=token_out.access_token),
    )


@auth_router.post(
    path="/logout", # TODO 后续可能会有复杂的登出策略
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie(description="刷新令牌")] = None,
) -> SuccessResponse[None]:
    """用户登出接口"""
    if refresh_token:
        await delete_refresh_token(refresh_token)
        
    response.delete_cookie(
        key="refresh_token",
        path=REFRESH_PATH,
        httponly=True,
        secure=ENV == "production",
        samesite="lax",
    )
    return SuccessResponse[None](message="登出成功")
