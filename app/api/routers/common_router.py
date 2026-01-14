from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_captcha_service
from app.common.constants import (
    CAPTCHA_GENERATE_SUCCESS,
)
from app.schemas import (
    CaptchaOut,
    SuccessResponse,
)
from app.services import CaptchaService
from app.utils import (
    RateLimiter,
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
