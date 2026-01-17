from .admin_router import router as admin_router
from .auth_router import auth_router
from .category_router import category_router
from .common_router import common_router
from .merchant_router import merchant_router
from .product_router import product_router
from .user_router import user_router

__all__ = [
    "admin_router",
    "auth_router",
    "category_router",
    "common_router",
    "merchant_router",
    "product_router",
    "user_router",
]
