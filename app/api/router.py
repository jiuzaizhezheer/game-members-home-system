from fastapi import APIRouter

from app.api.routers import (
    auth_router,
    common_router,
    user_router,
)

# API routers
api_routers = APIRouter(prefix="/api")

api_routers.include_router(user_router, prefix="/users", tags=["users"])
api_routers.include_router(auth_router, prefix="/auth", tags=["auth"])
api_routers.include_router(common_router, prefix="/commons", tags=["commons"])
