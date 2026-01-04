from fastapi import Request

from app.services import CaptchaService, UserService


def get_user_service(request: Request) -> UserService:
    return request.app.state.user_service


def get_captcha_service(request: Request) -> CaptchaService:
    return request.app.state.captcha_service


def get_current_user_id(request: Request) -> str:
    """
    从 request.state 中获取当前登录用户的 ID
    必须配合 RoleChecker 使用
    """
    if not hasattr(request.state, "user_id") or not request.state.user_id:
        # 防止没有调用 RoleChecker 直接使用该依赖的情况
        raise RuntimeError(
            "User ID not found in request state. Is RoleChecker middleware active?"
        )
    return str(request.state.user_id)
