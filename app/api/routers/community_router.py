from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Request, status

from app.api.deps import (
    get_community_service,
    get_current_user_id,
    get_optional_user_id,
)
from app.api.role import require_member
from app.common.constants import GET_SUCCESS, POST_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.community import (
    CommentCreateIn,
    CommentItemOut,
    CommentListOut,
    GroupDetailOut,
    GroupListOut,
    LikeToggleIn,
    PostCreateIn,
    PostDetailOut,
    PostListOut,
    PostUpdateIn,
)
from app.services.community_service import CommunityService

community_router = APIRouter()

# --- Groups ---


@community_router.get(
    "/groups",
    response_model=SuccessResponse[GroupListOut],
    status_code=status.HTTP_200_OK,
)
async def get_groups(
    service: Annotated[CommunityService, Depends(get_community_service)],
    user_id: Annotated[str | None, Depends(get_optional_user_id)] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取社群列表"""
    data = await service.get_groups(user_id, page, page_size)
    return SuccessResponse[GroupListOut](message=GET_SUCCESS, data=data)


@community_router.get(
    "/groups/{group_id}",
    response_model=SuccessResponse[GroupDetailOut],
    status_code=status.HTTP_200_OK,
)
async def get_group_detail(
    group_id: Annotated[str, Path()],
    service: Annotated[CommunityService, Depends(get_community_service)],
    user_id: Annotated[str | None, Depends(get_optional_user_id)] = None,
):
    """获取社群详情"""
    data = await service.get_group_detail(group_id, user_id)
    return SuccessResponse[GroupDetailOut](message=GET_SUCCESS, data=data)


@community_router.post(
    "/groups/{group_id}/join",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    dependencies=[require_member],
)
async def join_group(
    group_id: Annotated[str, Path()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[CommunityService, Depends(get_community_service)],
):
    """加入社群"""
    await service.join_group(user_id, group_id)
    return SuccessResponse[None](message="Joined successfully")


@community_router.post(
    "/groups/{group_id}/leave",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    dependencies=[require_member],
)
async def leave_group(
    group_id: Annotated[str, Path()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[CommunityService, Depends(get_community_service)],
):
    """退出社群"""
    await service.leave_group(user_id, group_id)
    return SuccessResponse[None](message="Left successfully")


# --- Posts ---


@community_router.get(
    "/groups/{group_id}/posts",
    response_model=SuccessResponse[PostListOut],
    status_code=status.HTTP_200_OK,
)
async def get_group_posts(
    group_id: Annotated[str, Path()],
    service: Annotated[CommunityService, Depends(get_community_service)],
    user_id: Annotated[str | None, Depends(get_optional_user_id)] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取社群帖子列表"""
    data = await service.get_posts(group_id, user_id, page, page_size)
    return SuccessResponse[PostListOut](message=GET_SUCCESS, data=data)


@community_router.post(
    "/posts",
    response_model=SuccessResponse[PostDetailOut],
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_member],
)
async def create_post(
    payload: Annotated[PostCreateIn, Body()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[CommunityService, Depends(get_community_service)],
):
    """发布帖子"""
    data = await service.create_post(user_id, payload)
    return SuccessResponse[PostDetailOut](message=POST_SUCCESS, data=data)


@community_router.put(
    "/posts/{post_id}",
    response_model=SuccessResponse[PostDetailOut],
    status_code=status.HTTP_200_OK,
    dependencies=[require_member],
)
async def update_post(
    post_id: Annotated[str, Path()],
    payload: Annotated[PostUpdateIn, Body()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[CommunityService, Depends(get_community_service)],
):
    """更新帖子"""
    data = await service.update_post(post_id, user_id, payload)
    return SuccessResponse[PostDetailOut](message="Updated successfully", data=data)


@community_router.get(
    "/posts/{post_id}",
    response_model=SuccessResponse[PostDetailOut],
    status_code=status.HTTP_200_OK,
)
async def get_post_detail(
    request: Request,
    post_id: Annotated[str, Path()],
    service: Annotated[CommunityService, Depends(get_community_service)],
    user_id: Annotated[str | None, Depends(get_optional_user_id)] = None,
):
    """获取帖子详情"""
    ip_address = request.client.host if request.client else "unknown"
    data = await service.get_post_detail(post_id, user_id, ip_address)
    return SuccessResponse[PostDetailOut](message=GET_SUCCESS, data=data)


@community_router.get(
    "/my-posts",
    response_model=SuccessResponse[PostListOut],
    status_code=status.HTTP_200_OK,
    dependencies=[require_member],
)
async def get_my_posts(
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[CommunityService, Depends(get_community_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取登录用户的帖子列表"""
    data = await service.get_user_posts(user_id, page, page_size)
    return SuccessResponse[PostListOut](message=GET_SUCCESS, data=data)


@community_router.get(
    "/search",
    response_model=SuccessResponse[PostListOut],
    status_code=status.HTTP_200_OK,
)
async def search_posts(
    query: Annotated[str, Query(min_length=1)],
    service: Annotated[CommunityService, Depends(get_community_service)],
    user_id: Annotated[str | None, Depends(get_optional_user_id)] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """全局搜索帖子"""
    data = await service.search_posts(query, user_id, page, page_size)
    return SuccessResponse[PostListOut](message=GET_SUCCESS, data=data)


# --- Comments ---


@community_router.post(
    "/posts/{post_id}/comments",
    response_model=SuccessResponse[CommentItemOut],
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_member],
)
async def create_comment(
    post_id: Annotated[str, Path()],
    payload: Annotated[CommentCreateIn, Body()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[CommunityService, Depends(get_community_service)],
):
    """发布评论"""
    data = await service.create_comment(user_id, post_id, payload)
    return SuccessResponse[CommentItemOut](message=POST_SUCCESS, data=data)


@community_router.get(
    "/posts/{post_id}/comments",
    response_model=SuccessResponse[CommentListOut],
    status_code=status.HTTP_200_OK,
)
async def get_post_comments(
    post_id: Annotated[str, Path()],
    service: Annotated[CommunityService, Depends(get_community_service)],
    user_id: Annotated[str | None, Depends(get_optional_user_id)] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取评论列表"""
    data = await service.get_comments(post_id, user_id, page, page_size)
    return SuccessResponse[CommentListOut](message=GET_SUCCESS, data=data)


# --- Likes ---


@community_router.post(
    "/likes",
    response_model=SuccessResponse[bool],
    status_code=status.HTTP_200_OK,
    dependencies=[require_member],
)
async def toggle_like(
    payload: Annotated[LikeToggleIn, Body()],
    user_id: Annotated[str, Depends(get_current_user_id)],
    service: Annotated[CommunityService, Depends(get_community_service)],
):
    """点赞/取消点赞"""
    is_liked = await service.toggle_like(
        user_id, str(payload.target_id), payload.target_type
    )
    msg = "Liked" if is_liked else "Unliked"
    return SuccessResponse[bool](message=msg, data=is_liked)
