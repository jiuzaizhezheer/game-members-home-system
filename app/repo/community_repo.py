"""Community Repository Layer"""

import uuid
from collections.abc import Sequence
from typing import cast

from beanie import PydanticObjectId
from sqlalchemy import and_, delete, desc, exists, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.mongodb.comments import Comment
from app.entity.mongodb.likes import Like as MongoLike
from app.entity.pgsql import (
    CommunityGroup,
    GroupMember,
    Post,
    User,
)

# --- Groups ---


async def create_group(session: AsyncSession, group: CommunityGroup) -> CommunityGroup:
    session.add(group)
    await session.flush()
    await session.refresh(group)
    return group


async def update_group(
    session: AsyncSession, group_id: uuid.UUID, **kwargs
) -> CommunityGroup:
    stmt = (
        update(CommunityGroup)
        .where(CommunityGroup.id == group_id)
        .values(**kwargs)
        .returning(CommunityGroup)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_groups_by_merchant(
    session: AsyncSession, merchant_id: uuid.UUID, page: int, page_size: int
) -> tuple[Sequence[CommunityGroup], int]:
    stmt = (
        select(CommunityGroup)
        .where(
            CommunityGroup.merchant_id == merchant_id,
            CommunityGroup.is_active.is_(True),
        )
        .order_by(CommunityGroup.created_at.desc())
    )

    total = (
        await session.scalar(
            select(func.count())
            .select_from(CommunityGroup)
            .where(
                CommunityGroup.merchant_id == merchant_id,
                CommunityGroup.is_active.is_(True),
            )
        )
        or 0
    )

    result = await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total


async def exists_by_name(session: AsyncSession, name: str) -> bool:
    """Check if a group with the same name exists."""
    stmt = select(exists().where(CommunityGroup.name == name))
    return bool((await session.execute(stmt)).scalar())


async def get_group_list(
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[CommunityGroup], int]:
    """Get group list with optional joined status if user_id provided"""
    stmt = select(CommunityGroup).where(CommunityGroup.is_active.is_(True))

    # Count total
    count_stmt = (
        select(func.count())
        .select_from(CommunityGroup)
        .where(CommunityGroup.is_active.is_(True))
    )
    total = (await session.execute(count_stmt)).scalar() or 0

    # Paging
    stmt = stmt.order_by(
        desc(CommunityGroup.member_count), desc(CommunityGroup.created_at)
    )
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    groups = result.scalars().all()

    return groups, total


async def get_group_by_id(
    session: AsyncSession, group_id: uuid.UUID
) -> CommunityGroup | None:
    return await session.get(CommunityGroup, group_id)


async def check_joined(
    session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID
) -> bool:
    stmt = select(
        exists().where(GroupMember.user_id == user_id, GroupMember.group_id == group_id)
    )
    return bool((await session.execute(stmt)).scalar())


async def join_group(
    session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID
) -> None:
    try:
        member = GroupMember(user_id=user_id, group_id=group_id)
        session.add(member)
        # atomic increment member_count
        await session.flush()  # Ensure Unique Constraint check
        await session.execute(
            update(CommunityGroup)
            .where(CommunityGroup.id == group_id)
            .values(member_count=CommunityGroup.member_count + 1)
        )
    except IntegrityError:
        # Already joined, ignore
        await session.rollback()


async def leave_group(
    session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID
) -> None:
    stmt = delete(GroupMember).where(
        GroupMember.user_id == user_id, GroupMember.group_id == group_id
    )
    result = cast(CursorResult, await session.execute(stmt))
    if (result.rowcount or 0) > 0:
        await session.execute(
            update(CommunityGroup)
            .where(CommunityGroup.id == group_id)
            .values(member_count=CommunityGroup.member_count - 1)
        )


# --- Posts ---


async def create_post(session: AsyncSession, post: Post) -> Post:
    session.add(post)
    await session.flush()
    # atomic increment group post_count
    await session.execute(
        update(CommunityGroup)
        .where(CommunityGroup.id == post.group_id)
        .values(post_count=CommunityGroup.post_count + 1)
    )
    await session.refresh(post)
    return post


async def update_post(
    session: AsyncSession, post_id: uuid.UUID, **kwargs
) -> Post | None:
    """Update post fields dynamically."""
    stmt = update(Post).where(Post.id == post_id).values(**kwargs).returning(Post)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def toggle_hide_post(
    session: AsyncSession, post_id: uuid.UUID, is_hidden: bool
) -> Post | None:
    stmt = (
        update(Post)
        .where(Post.id == post_id)
        .values(is_hidden=is_hidden)
        .returning(Post)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_post_list(
    session: AsyncSession,
    group_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[tuple[Post, User]], int]:
    """Get posts in a group with author info"""
    base_query = (
        select(Post, User)
        .join(User, Post.user_id == User.id)
        .where(Post.group_id == group_id, Post.is_hidden.is_(False))
    )

    # Count
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # List (Top first, then newest)
    stmt = base_query.order_by(desc(Post.is_top), desc(Post.created_at))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    return result.tuples().all(), total


async def get_posts_by_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[tuple[Post, User, CommunityGroup]], int]:
    """获取特定用户的帖子列表，包含圈子和作者信息"""
    base_query = (
        select(Post, User, CommunityGroup)
        .join(User, Post.user_id == User.id)
        .join(CommunityGroup, Post.group_id == CommunityGroup.id)
        .where(Post.user_id == user_id)
    )

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = base_query.order_by(desc(Post.created_at))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    return result.tuples().all(), total


async def search_posts(
    session: AsyncSession,
    query_text: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[tuple[Post, User, CommunityGroup]], int]:
    """全局搜索帖子 (标题或内容包含关键字)"""
    pattern = f"%{query_text}%"
    base_query = (
        select(Post, User, CommunityGroup)
        .join(User, Post.user_id == User.id)
        .join(CommunityGroup, Post.group_id == CommunityGroup.id)
        .where(
            and_(
                Post.is_hidden.is_(False),
                (Post.title.ilike(pattern) | Post.content.ilike(pattern)),
            )
        )
    )

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = base_query.order_by(desc(Post.created_at))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    return result.tuples().all(), total


async def get_posts_by_merchant(
    session: AsyncSession,
    merchant_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[tuple[Post, User, CommunityGroup]], int]:
    """Get posts in all groups belonging to a merchant"""
    base_query = (
        select(Post, User, CommunityGroup)
        .join(User, Post.user_id == User.id)
        .join(CommunityGroup, Post.group_id == CommunityGroup.id)
        .where(CommunityGroup.merchant_id == merchant_id)
    )

    # Count
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # List (Newest first)
    stmt = base_query.order_by(desc(Post.created_at))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    return result.tuples().all(), total


async def get_post_detail(
    session: AsyncSession, post_id: uuid.UUID
) -> tuple[Post, User, CommunityGroup] | None:
    stmt = (
        select(Post, User, CommunityGroup)
        .join(User, Post.user_id == User.id)
        .join(CommunityGroup, Post.group_id == CommunityGroup.id)
        .where(Post.id == post_id)
    )
    result = await session.execute(stmt)
    row = result.first()
    if row:
        return row  # type: ignore
    return None


async def delete_post(session: AsyncSession, post_id: uuid.UUID) -> None:
    # Need to decrement group post count first?
    post = await session.get(Post, post_id)
    if not post:
        return

    await session.delete(post)
    await session.execute(
        update(CommunityGroup)
        .where(CommunityGroup.id == post.group_id)
        .values(post_count=CommunityGroup.post_count - 1)
    )


async def increment_view(session: AsyncSession, post_id: uuid.UUID) -> None:
    await session.execute(
        update(Post).where(Post.id == post_id).values(view_count=Post.view_count + 1)
    )


# --- Comments ---


async def create_comment(session: AsyncSession, comment: Comment) -> Comment:
    # 1. Save to MongoDB
    await comment.insert()

    # 2. Update Post comment_count in PG
    # Note: Not transactional across DBs
    await session.execute(
        update(Post)
        .where(Post.id == comment.post_id)
        .values(comment_count=Post.comment_count + 1)
    )
    return comment


async def get_comment_list(
    session: AsyncSession,  # kept for signature consistency, unused for query
    post_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[Comment], int]:
    # Query MongoDB
    # TODO: Add proper filtering/sorting
    # Assuming comments are flat for now or this is getting root comments

    query = Comment.find(Comment.post_id == post_id)
    total = await query.count()

    comments = (
        await query.sort("created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )

    return comments, total


# --- Likes ---


async def check_liked(
    session: AsyncSession,
    user_id: uuid.UUID,
    target_id: str | uuid.UUID,
    target_type: str,
) -> bool:
    try:
        tid: uuid.UUID | PydanticObjectId
        if target_type in {"post", "product"}:
            tid = (
                target_id
                if isinstance(target_id, uuid.UUID)
                else uuid.UUID(str(target_id))
            )
        else:
            tid = PydanticObjectId(str(target_id))
    except (ValueError, TypeError):
        return False

    count = await MongoLike.find(
        {"user_id": user_id, "target_id": tid, "target_type": target_type}
    ).count()
    return count > 0


async def toggle_like(
    session: AsyncSession, user_id: uuid.UUID, target_id: str, target_type: str
) -> bool:
    """Toggle like status using MongoDB. Returns True if liked, False if unliked."""
    try:
        tid: uuid.UUID | PydanticObjectId
        if target_type in {"post", "product"}:
            tid = uuid.UUID(target_id)
        else:
            tid = PydanticObjectId(target_id)
    except (ValueError, TypeError):
        # Invalid ID format for type
        return False

    # Check if exists in Mongo
    # Check if exists in Mongo
    existing = await MongoLike.find_one(
        {"user_id": user_id, "target_id": tid, "target_type": target_type}
    )

    is_liked = False
    delta = 0

    if existing:
        # Unlike
        await existing.delete()
        delta = -1
        is_liked = False
    else:
        # Like
        new_like = MongoLike(user_id=user_id, target_id=tid, target_type=target_type)
        await new_like.insert()
        delta = 1
        is_liked = True

    # Update stats
    if target_type == "post":
        # Post in PG (tid is UUID)
        stmt = update(Post).where(Post.id == tid)
        if delta > 0:
            stmt = stmt.values(likes_count=Post.likes_count + delta)
        else:
            # Prevent negative count
            stmt = stmt.values(likes_count=func.greatest(0, Post.likes_count + delta))
        await session.execute(stmt)

    elif target_type == "product":
        # Product in PG (tid is UUID)
        from app.repo import products_repo

        await products_repo.change_likes_count(session, cast(uuid.UUID, tid), delta)

    elif target_type == "comment":
        # Comment in Mongo (tid is ObjectId)
        # Need to fetch comment first
        comment = await Comment.find_one(Comment.id == tid)
        if comment:
            comment.likes_count += delta
            if comment.likes_count < 0:
                comment.likes_count = 0
            await comment.save()

    return is_liked
