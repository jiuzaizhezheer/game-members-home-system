from fastapi import APIRouter

from app.api.routers import (
    admin_router,
    auth_router,
    category_router,
    common_router,
    merchant_router,
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
api_routers.include_router(admin_router, prefix="/admin", tags=["admin"])
