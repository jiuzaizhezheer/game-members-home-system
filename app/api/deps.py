from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services import (
    AddressService,
    AuthService,
    CaptchaService,
    CartService,
    CategoryService,
    CommunityService,
    FavoriteService,
    MerchantService,
    MessageService,
    OrderService,
    ProductService,
    PromotionService,
    UserService,
)
from app.utils import decode_access_token

# 单例模式
_user_service = UserService()
_auth_service = AuthService()
_captcha_service = CaptchaService()
_merchant_service = MerchantService()
_product_service = ProductService()
_category_service = CategoryService()
_cart_service = CartService()
_address_service = AddressService()
_order_service = OrderService()
_favorite_service = FavoriteService()
_message_service = MessageService()
_community_service = CommunityService()
_promotion_service = PromotionService()


def get_user_service() -> UserService:
    return _user_service


def get_auth_service() -> AuthService:
    return _auth_service


def get_captcha_service() -> CaptchaService:
    return _captcha_service


def get_merchant_service() -> MerchantService:
    return _merchant_service


def get_product_service() -> ProductService:
    return _product_service


def get_category_service() -> CategoryService:
    return _category_service


def get_address_service() -> AddressService:
    return _address_service


def get_order_service() -> OrderService:
    return _order_service


def get_cart_service() -> CartService:
    return _cart_service


def get_favorite_service() -> FavoriteService:
    return _favorite_service


def get_message_service() -> MessageService:
    return _message_service


def get_community_service() -> CommunityService:
    return _community_service


def get_promotion_service() -> PromotionService:
    return _promotion_service


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


async def get_optional_user_id(
    token_credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))
    ],
) -> str | None:
    """
    尝试从 Authorization 头获取用户 ID，但不强制要求登录
    """
    if not token_credentials:
        return None

    try:
        payload = decode_access_token(token_credentials.credentials)
        user_id = payload.get("sub")
        return str(user_id) if user_id else None
    except Exception:
        # 无论是过期还是无效，可选模式下都视为匿名用户
        return None
