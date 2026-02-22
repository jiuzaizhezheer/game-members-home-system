"""管理员 — 社区内容审核仓储层"""

import uuid
from collections.abc import Sequence

from beanie import PydanticObjectId
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.mongodb.comments import Comment
from app.entity.pgsql import CommunityGroup, Post, User


async def get_all_posts(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    is_hidden: bool | None = None,
) -> tuple[Sequence[tuple[Post, User, CommunityGroup]], int]:
    """全平台帖子列表（管理员视角，含隐藏帖子）"""
    base = (
        select(Post, User, CommunityGroup)
        .join(User, Post.user_id == User.id)
        .join(CommunityGroup, Post.group_id == CommunityGroup.id)
    )

    if keyword:
        pattern = f"%{keyword}%"
        base = base.where(or_(Post.title.ilike(pattern), Post.content.ilike(pattern)))

    if is_hidden is not None:
        base = base.where(Post.is_hidden == is_hidden)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = base.order_by(desc(Post.created_at))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    return result.tuples().all(), total


async def get_all_comments(
    *,
    page: int = 1,
    page_size: int = 20,
    post_id: str | None = None,
) -> tuple[list[Comment], int]:
    """全平台评论列表（管理员视角）"""
    query = Comment.find()

    if post_id:
        query = Comment.find(Comment.post_id == uuid.UUID(post_id))

    total = await query.count()

    comments = (
        await query.sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )

    return comments, total


async def delete_comment(comment_id: str) -> bool:
    """删除评论"""
    comment = await Comment.get(PydanticObjectId(comment_id))
    if not comment:
        return False
    await comment.delete()
    return True
