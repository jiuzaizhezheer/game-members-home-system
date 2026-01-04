from fastapi import APIRouter

from app.api.routers.common_router import router as common_router
from app.api.routers.user_router import router as user_router

api_router = APIRouter()
api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(common_router, prefix="/commons", tags=["commons"])
