from .address_router import address_router
from .admin_community_router import admin_community_router
from .admin_log_router import admin_log_router
from .admin_merchant_router import admin_merchant_router
from .admin_product_router import admin_product_router
from .admin_router import router as admin_router
from .admin_user_router import admin_user_router
from .auth_router import auth_router
from .cart_router import cart_router
from .category_router import category_router
from .common_router import common_router
from .community_router import community_router
from .favorite_router import favorite_router
from .merchant_community_router import merchant_community_router
from .merchant_promotion_router import merchant_promotion_router
from .merchant_router import merchant_router
from .merchant_statistics_router import merchant_statistics_router
from .message_router import message_router
from .order_router import order_router
from .product_router import product_router
from .user_router import user_router

__all__ = [
    "admin_community_router",
    "admin_log_router",
    "admin_merchant_router",
    "admin_product_router",
    "admin_router",
    "admin_user_router",
    "auth_router",
    "category_router",
    "common_router",
    "community_router",
    "favorite_router",
    "merchant_community_router",
    "merchant_promotion_router",
    "merchant_router",
    "merchant_statistics_router",
    "product_router",
    "user_router",
    "cart_router",
    "address_router",
    "order_router",
    "message_router",
]
