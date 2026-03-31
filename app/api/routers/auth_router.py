from typing import Annotated

from fastapi import APIRouter, Body, Cookie, Depends, Response, status

from app.api.deps import get_auth_service, get_captcha_service
from app.common.constants import (
    CAPTCHA_GENERATE_SUCCESS,
    INVALID_EMAIL_CAPTCHA,
    INVALID_IMAGE_CAPTCHA,
    LOGIN_SUCCESS,
    REFRESH_TOKEN_SUCCESS,
    REGISTER_SUCCESS,
)
from app.common.errors import ValidationError
from app.core.config import ENV, REFRESH_TOKEN_EXPIRE_DAYS
from app.schemas import (
    AccessTokenOut,
    AuthLoginIn,
    AuthRegisterIn,
    CaptchaOut,
    EmailCaptchaIn,
    EmailCaptchaOut,
    SuccessResponse,
)
from app.tasks.tasks import send_verification_email_task
from app.services import AuthService, CaptchaService
from app.utils import RateLimiter, delete_refresh_token

auth_router = APIRouter()
# Cookie path 需要覆盖 /refresh 和 /logout 两个接口
COOKIE_PATH = "/api/auths"


@auth_router.get(
    path="/captcha",
    dependencies=[Depends(RateLimiter(counts=9999, seconds=30))],
    response_model=SuccessResponse[CaptchaOut],
    status_code=status.HTTP_200_OK,
)
async def generate_captcha(
    captcha_service: Annotated[CaptchaService, Depends(get_captcha_service)],
) -> SuccessResponse[CaptchaOut]:
    """生成图片验证码路由
    返回：
    - id: 验证码唯一标识（注册/登录时附带）
    - image: data:image/svg+xml;base64,... 直接用于 <img src="...">
    """
    captcha = await captcha_service.create_captcha()
    return SuccessResponse[CaptchaOut](message=CAPTCHA_GENERATE_SUCCESS, data=captcha)


@auth_router.post(
    path="/captcha/email",
    dependencies=[Depends(RateLimiter(counts=10, seconds=60))],
    response_model=SuccessResponse[EmailCaptchaOut],  # TODO
    status_code=status.HTTP_200_OK,
)
async def generate_email_captcha(
    payload: EmailCaptchaIn,
    captcha_service: Annotated[CaptchaService, Depends(get_captcha_service)],
) -> SuccessResponse[EmailCaptchaOut]:
    """向指定邮箱发送验证码路由
    返回：
    - id: 验证码唯一标识（注册/登录时附带）
    """
    is_valid = await captcha_service.verify_image_captcha(
        payload.image_captcha_id,
        payload.image_captcha_code,
    )
    if not is_valid:
        raise ValidationError(detail=INVALID_IMAGE_CAPTCHA)

    captcha_id, code = await captcha_service.create_email_captcha()

    # 将发信任务交给 Taskiq 异步 Worker 处理，更加可靠且支持重试

    await send_verification_email_task.kiq(payload.email, code)

    captcha_out = EmailCaptchaOut(id=captcha_id)
    return SuccessResponse[EmailCaptchaOut](
        message="验证码已发送至您的邮箱，请查收", data=captcha_out
    )


@auth_router.post(
    path="/register",
    dependencies=[Depends(RateLimiter(counts=99999, seconds=60))],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: Annotated[AuthRegisterIn, Body(description="注册请求体")],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    captcha_service: Annotated[CaptchaService, Depends(get_captcha_service)],
) -> SuccessResponse[None]:
    """用户注册接口路由"""
    is_valid = await captcha_service.verify_email_captcha(
        payload.captcha_id,
        payload.captcha_code,
    )
    if not is_valid:
        raise ValidationError(detail=INVALID_EMAIL_CAPTCHA)

    await auth_service.register(payload)
    return SuccessResponse[None](message=REGISTER_SUCCESS)


@auth_router.post(
    path="/login",
    dependencies=[Depends(RateLimiter(counts=9999, seconds=60))],
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
        secure=ENV == "production",  # TODO 根据环境决定是否开启
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 7 天
        path=COOKIE_PATH,
    )

    return SuccessResponse[AccessTokenOut](
        message=LOGIN_SUCCESS,
        data=AccessTokenOut(access_token=token_out.access_token),
    )


@auth_router.post(
    path="/refresh",
    dependencies=[Depends(RateLimiter(counts=9999, seconds=60))],
    response_model=SuccessResponse[AccessTokenOut],
    status_code=status.HTTP_200_OK,
)
async def refresh_all_token(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[str | None, Cookie(description="刷新令牌")] = None,
) -> SuccessResponse[AccessTokenOut]:
    """
    刷新令牌接口路由
    从 Cookie 中获取 refresh_token，返回新的 access_token
    """
    token_out = await auth_service.refresh_all_token(refresh_token)
    # 刷新 Cookie
    response.set_cookie(
        key="refresh_token",
        value=token_out.refresh_token,
        httponly=True,
        secure=ENV == "production",
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=COOKIE_PATH,
    )

    return SuccessResponse[AccessTokenOut](
        message=REFRESH_TOKEN_SUCCESS,
        data=AccessTokenOut(access_token=token_out.access_token),
    )


@auth_router.post(
    path="/logout",  # TODO 后续可能会有复杂的登出策略
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
            httponly=True,
            secure=ENV == "production",
            samesite="lax",
            path=COOKIE_PATH,
        )
    return SuccessResponse[None](message="登出成功")
