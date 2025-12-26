from fastapi import Request

from app.services import AuthService, CaptchaService


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_captcha_service(request: Request) -> CaptchaService:
    return request.app.state.captcha_service
