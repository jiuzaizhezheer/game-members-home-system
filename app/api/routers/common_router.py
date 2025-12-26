from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_captcha_service
from app.services.captcha_service import CaptchaService

router = APIRouter()


@router.get("/captcha", tags=["common"])
async def generate_captcha(
    captcha_service: Annotated[CaptchaService, Depends(get_captcha_service)]
):
    """生成图片验证码
    返回：
    - id: 验证码唯一标识（注册/登录时附带）
    - image: data:image/svg+xml;base64,... 直接用于 <img src="...">
    """
    return await captcha_service.create_captcha()
