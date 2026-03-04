from fastapi import APIRouter, Query

from app.api.role import require_admin
from app.common.constants import (
    CREATE_SUCCESS,
    DELETE_SUCCESS,
    GET_SUCCESS,
    UPDATE_SUCCESS,
)
from app.schemas import SuccessResponse
from app.schemas.banner import BannerIn, BannerListOut, BannerOut, BannerUpdateIn
from app.services.banner_service import banner_service

router = APIRouter()


@router.get("", response_model=SuccessResponse[BannerListOut])
async def list_banners(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin=require_admin,
):
    """(Admin) 获取 Banner 列表"""
    data = await banner_service.get_admin_banners(page, page_size)
    return SuccessResponse(data=data, message=GET_SUCCESS)


@router.post("", response_model=SuccessResponse[BannerOut])
async def create_banner(
    payload: BannerIn,
    _admin=require_admin,
):
    """(Admin) 创建 Banner"""
    data = await banner_service.create_banner(payload)
    return SuccessResponse(data=data, message=CREATE_SUCCESS)


@router.patch("/{id}", response_model=SuccessResponse[BannerOut])
async def update_banner(
    id: str,
    payload: BannerUpdateIn,
    _admin=require_admin,
):
    """(Admin) 更新 Banner"""
    data = await banner_service.update_banner(id, payload)
    return SuccessResponse(data=data, message=UPDATE_SUCCESS)


@router.delete("/{id}", response_model=SuccessResponse[None])
async def delete_banner(
    id: str,
    _admin=require_admin,
):
    """(Admin) 删除 Banner"""
    await banner_service.delete_banner(id)
    return SuccessResponse(message=DELETE_SUCCESS)
