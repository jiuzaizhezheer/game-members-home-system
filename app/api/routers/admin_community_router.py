"""
管理员 — 社群与内容审核路由
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import get_admin_service, get_community_service, get_current_user_id
from app.api.role import require_admin
from app.common.constants import GET_SUCCESS, POST_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.community import (
    CommentListOut,
    GroupCreateIn,
    GroupDetailOut,
    PostListOut,
)
from app.services import AdminService, CommunityService

admin_community_router = APIRouter()


# --- 话题圈管理 ---


@admin_community_router.post(
    path="/groups",
    dependencies=[require_admin],
    response_model=SuccessResponse[GroupDetailOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_community_group(
    payload: GroupCreateIn,
    community_service: Annotated[CommunityService, Depends(get_community_service)],
):
    """管理员创建话题圈"""
    data = await community_service.create_group(payload)
    return SuccessResponse[GroupDetailOut](message=POST_SUCCESS, data=data)


# --- 帖子审核 ---


@admin_community_router.get(
    path="/posts",
    dependencies=[require_admin],
    response_model=SuccessResponse[PostListOut],
    status_code=status.HTTP_200_OK,
)
async def get_post_list(
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    keyword: Annotated[str | None, Query(description="标题/内容搜索")] = None,
    is_hidden: Annotated[bool | None, Query(description="是否隐藏筛选")] = None,
) -> SuccessResponse[PostListOut]:
    """管理员查看全平台帖子列表"""
    data = await admin_service.get_all_posts(
        page=page, page_size=page_size, keyword=keyword, is_hidden=is_hidden
    )
    return SuccessResponse[PostListOut](message=GET_SUCCESS, data=data)


@admin_community_router.patch(
    path="/posts/{id}/review",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def review_post(
    id: Annotated[str, Path(description="帖子ID")],
    is_hidden: Annotated[bool, Query(description="是否隐藏")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    admin_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[None]:
    """管理员审核帖子（隐藏/显示）"""
    await admin_service.review_post(id, is_hidden, admin_id=admin_id)
    return SuccessResponse[None](message=POST_SUCCESS)


@admin_community_router.delete(
    path="/posts/{id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def delete_post(
    id: Annotated[str, Path(description="帖子ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    admin_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[None]:
    """管理员删除帖子"""
    await admin_service.delete_post(id, admin_id=admin_id)
    return SuccessResponse[None](message=POST_SUCCESS)


# --- 评论管理 ---


@admin_community_router.get(
    path="/comments",
    dependencies=[require_admin],
    response_model=SuccessResponse[CommentListOut],
    status_code=status.HTTP_200_OK,
)
async def get_comment_list(
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    post_id: Annotated[str | None, Query(description="按帖子ID筛选")] = None,
) -> SuccessResponse[CommentListOut]:
    """管理员查看全平台评论列表"""
    data = await admin_service.get_all_comments(
        page=page, page_size=page_size, post_id=post_id
    )
    return SuccessResponse[CommentListOut](message=GET_SUCCESS, data=data)


@admin_community_router.delete(
    path="/comments/{id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def delete_comment(
    id: Annotated[str, Path(description="评论ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
    admin_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[None]:
    """管理员删除评论"""
    await admin_service.delete_comment(id, admin_id=admin_id)
    return SuccessResponse[None](message=POST_SUCCESS)
