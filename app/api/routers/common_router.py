from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.api.deps import get_captcha_service
from app.common.constants import (
    CAPTCHA_GENERATE_SUCCESS,
    REFRESH_TOKEN_INVALID,
    REFRESH_TOKEN_SUCCESS,
)
from app.common.errors import ValidationError
from app.schemas import (
    CaptchaOut,
    SuccessResponse,
    TokenOut,
)
from app.services import CaptchaService
from app.utils import (
    RateLimiter,
    delete_refresh_token,
    get_access_token,
    get_refresh_token,
    verify_refresh_token,
)

common_router = APIRouter()


@common_router.get(
    path="/captcha",  # TODO: 后续可能修改为向邮箱发送验证码
    dependencies=[Depends(RateLimiter(counts=2, seconds=30))],
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


@common_router.post(
    path="/token-refresh",
    dependencies=[Depends(RateLimiter(counts=1, seconds=60))],
    response_model=SuccessResponse[TokenOut],
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    refresh_token: Annotated[str, Body(description="刷新令牌", embed=True)],
) -> SuccessResponse[TokenOut]:
    """
    刷新令牌接口路由
    使用有效的 refresh_token 获取新的一对 access_token 和 refresh_token
    """
    # 1. 验证 refresh_token 是否存在于 Redis中
    token_data = await verify_refresh_token(refresh_token)
    if not token_data:
        raise ValidationError(REFRESH_TOKEN_INVALID)

    user_id = str(token_data.get("user_id"))
    role = str(token_data.get("role"))

    # 2. 生成新的 token
    new_access_token = get_access_token(user_id, role)
    new_refresh_token = await get_refresh_token(user_id, role)

    # 3. 删除旧的 refresh_token (Refresh Token Rotation 策略)
    await delete_refresh_token(refresh_token)

    token_out = TokenOut(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )
    return SuccessResponse[TokenOut](message=REFRESH_TOKEN_SUCCESS, data=token_out)
