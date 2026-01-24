from fastapi import Request

from app.services import AuthService, CaptchaService, UserService
from app.services.category_service import CategoryService
from app.services.merchant_service import MerchantService
from app.services.product_service import ProductService


def get_user_service(request: Request) -> UserService:
    return request.app.state.user_service


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_captcha_service(request: Request) -> CaptchaService:
    return request.app.state.captcha_service


def get_merchant_service(request: Request) -> MerchantService:
    return request.app.state.merchant_service


def get_product_service(request: Request) -> ProductService:
    return request.app.state.product_service


def get_category_service(request: Request) -> CategoryService:
    return request.app.state.category_service


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
