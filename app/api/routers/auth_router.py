from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_captcha_service
from app.common.constants import INVALID_CAPTCHA, LOGIN_SUCCESS, REGISTER_SUCCESS
from app.common.errors import ValidationError
from app.model import (
    LoginRequest,
    RegisterRequest,
    SuccessResponse,
    UserOut,
)
from app.services import AuthService, CaptchaService

router = APIRouter()


@router.post(
    "/register",
    response_model=SuccessResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    captcha_service: Annotated[CaptchaService, Depends(get_captcha_service)],
) -> SuccessResponse[UserOut]:

    is_valid = await captcha_service.verify_captcha(
        payload.captcha_id,
        payload.captcha_code,
    )
    if not is_valid:
        raise ValidationError(INVALID_CAPTCHA)

    user_out = await auth_service.register_user(payload)
    return SuccessResponse[UserOut](message=REGISTER_SUCCESS, data=user_out)


@router.post(
    "/login",
    response_model=SuccessResponse[UserOut],
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> SuccessResponse[UserOut]:
    user_out = await auth_service.login_user(payload)
    return SuccessResponse[UserOut](message=LOGIN_SUCCESS, data=user_out)
