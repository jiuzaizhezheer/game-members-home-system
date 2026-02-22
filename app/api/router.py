from fastapi import APIRouter

from app.api.routers import (
    address_router,
    admin_router,
    auth_router,
    cart_router,
    category_router,
    common_router,
    community_router,
    favorite_router,
    merchant_community_router,
    merchant_promotion_router,
    merchant_router,
    merchant_statistics_router,
    message_router,
    order_router,
    product_router,
    user_router,
)

# API routers
api_routers = APIRouter(prefix="/api")

# 资源路由
api_routers.include_router(user_router, prefix="/users", tags=["users"])
api_routers.include_router(auth_router, prefix="/auths", tags=["auths"])
api_routers.include_router(common_router, prefix="/commons", tags=["commons"])
api_routers.include_router(merchant_router, prefix="/merchants", tags=["merchants"])
api_routers.include_router(product_router, prefix="/products", tags=["products"])
api_routers.include_router(category_router, prefix="/categories", tags=["categories"])
api_routers.include_router(cart_router, prefix="/carts", tags=["cart"])
api_routers.include_router(address_router, prefix="/addresses", tags=["addresses"])
api_routers.include_router(order_router, prefix="/orders", tags=["orders"])
api_routers.include_router(favorite_router, prefix="/favorites", tags=["favorites"])
api_routers.include_router(message_router, prefix="/messages", tags=["messages"])
api_routers.include_router(community_router, prefix="/community", tags=["community"])
api_routers.include_router(
    merchant_community_router, prefix="/merchant/community", tags=["merchant-community"]
)
api_routers.include_router(
    merchant_promotion_router,
    prefix="/merchant/promotions",
    tags=["merchant-promotions"],
)
api_routers.include_router(
    merchant_statistics_router,
    prefix="/merchant/statistics",
    tags=["merchant-statistics"],
)
api_routers.include_router(admin_router, prefix="/admins", tags=["admin"])
