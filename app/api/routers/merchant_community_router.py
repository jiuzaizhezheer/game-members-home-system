from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import (
    get_community_service,
    get_current_user_id,
    get_merchant_service,
)
from app.api.role import require_merchant
from app.common.constants import (
    GET_SUCCESS,
    POST_SUCCESS,
)
from app.common.errors import PermissionDeniedError
from app.schemas import SuccessResponse
from app.schemas.community import (
    GroupCreateIn,
    GroupDetailOut,
    GroupListOut,
    GroupUpdateIn,
    PostListOut,
)
from app.services import CommunityService, MerchantService

merchant_community_router = APIRouter()

# --- Groups ---


@merchant_community_router.get(
    "/groups",
    dependencies=[require_merchant],
    response_model=SuccessResponse[GroupListOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_groups(
    user_id: Annotated[str, Depends(get_current_user_id)],
    community_service: Annotated[CommunityService, Depends(get_community_service)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取商家自己的社群列表"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    data = await community_service.get_merchant_groups(
        str(merchant.id), page, page_size
    )
    return SuccessResponse[GroupListOut](message=GET_SUCCESS, data=data)


@merchant_community_router.post(
    "/groups",
    dependencies=[require_merchant],
    response_model=SuccessResponse[GroupDetailOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_group(
    payload: Annotated[GroupCreateIn, Body()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    community_service: Annotated[CommunityService, Depends(get_community_service)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
):
    """商家创建社群"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    data = await community_service.create_group(payload, merchant_id=str(merchant.id))
    return SuccessResponse[GroupDetailOut](message=POST_SUCCESS, data=data)


@merchant_community_router.put(
    "/groups/{group_id}",
    dependencies=[require_merchant],
    response_model=SuccessResponse[GroupDetailOut],
    status_code=status.HTTP_200_OK,
)
async def update_group(
    group_id: Annotated[str, Path()],
    payload: Annotated[GroupUpdateIn, Body()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    community_service: Annotated[CommunityService, Depends(get_community_service)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
):
    """商家更新社群"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    # Assuming UpdateIn can map to CreateIn for service or service handles dict
    # Current service `update_group` accepts GroupCreateIn | dict
    # Ideally schema should align, but let's pass dict or cast
    data = await community_service.update_group(
        group_id, payload.model_dump(exclude_unset=True), merchant_id=str(merchant.id)
    )
    return SuccessResponse[GroupDetailOut](message="Updated successfully", data=data)


# --- Posts Moderation ---


@merchant_community_router.patch(
    "/posts/{post_id}/status",
    dependencies=[require_merchant],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def moderate_post(
    post_id: Annotated[str, Path()],
    is_hidden: Annotated[bool, Body(embed=True)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    community_service: Annotated[CommunityService, Depends(get_community_service)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
):
    """商家审核/隐藏帖子"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    await community_service.moderate_post(post_id, is_hidden, str(merchant.id))
    return SuccessResponse[None](message="Operation successful")


@merchant_community_router.get(
    "/posts",
    dependencies=[require_merchant],
    response_model=SuccessResponse[PostListOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_posts(
    user_id: Annotated[str, Depends(get_current_user_id)],
    community_service: Annotated[CommunityService, Depends(get_community_service)],
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取商家下属圈子的帖子列表（用于审核）"""
    merchant = await merchant_service.get_by_user_id(user_id)
    if not merchant:
        raise PermissionDeniedError("商家不存在")

    data = await community_service.get_merchant_posts(str(merchant.id), page, page_size)
    return SuccessResponse[PostListOut](message=GET_SUCCESS, data=data)
