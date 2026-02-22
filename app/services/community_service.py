"""Service Layer for Community Features"""

import uuid

from app.common.constants import COMMUNITY_GROUP_EXISTS, COMMUNITY_GROUP_NOT_FOUND
from app.common.errors import (
    DuplicateResourceError,
    NotFoundError,
    PermissionDeniedError,
)
from app.database.pgsql import get_pg
from app.entity.mongodb.comments import Comment, CommentUserRedundancy
from app.entity.pgsql import CommunityGroup, Post, User
from app.repo import community_repo
from app.schemas.community import (
    CommentCreateIn,
    CommentItemOut,
    CommentListOut,
    GroupCreateIn,
    GroupDetailOut,
    GroupItemOut,
    GroupListOut,
    PostCreateIn,
    PostDetailOut,
    PostItemOut,
    PostListOut,
    PostUpdateIn,
)
from app.utils import check_operation_lock


class CommunityService:

    # --- Groups ---

    async def create_group(
        self, payload: GroupCreateIn, merchant_id: str | None = None
    ) -> GroupDetailOut:
        """管理员或商家创建社群"""
        async with get_pg() as session:
            # 检查同名圈子
            if await community_repo.exists_by_name(session, payload.name):
                raise DuplicateResourceError(COMMUNITY_GROUP_EXISTS)

            group = CommunityGroup(
                name=payload.name,
                description=payload.description,
                cover_image=payload.cover_image,
                merchant_id=uuid.UUID(merchant_id) if merchant_id else None,
            )
            await community_repo.create_group(session, group)
            return GroupDetailOut.model_validate(group)

    async def update_group(
        self,
        group_id: str,
        payload: GroupCreateIn | dict,
        merchant_id: str | None = None,
    ) -> GroupDetailOut:
        gid = uuid.UUID(group_id)
        mid = uuid.UUID(merchant_id) if merchant_id else None

        async with get_pg() as session:
            group = await community_repo.get_group_by_id(session, gid)
            if not group:
                raise NotFoundError(COMMUNITY_GROUP_NOT_FOUND)

            # Check permission: internal admin (no merchant_id) or owner
            if mid and group.merchant_id != mid:
                raise PermissionDeniedError("无法修改非本商家的圈子")

            update_data = (
                payload.model_dump(exclude_unset=True)
                if not isinstance(payload, dict)
                else payload
            )
            # Filter out None/Internal fields if needed, but schema handles validation

            updated = await community_repo.update_group(session, gid, **update_data)
            return GroupDetailOut.model_validate(updated)

    async def get_merchant_groups(
        self, merchant_id: str, page: int = 1, page_size: int = 20
    ) -> GroupListOut:
        mid = uuid.UUID(merchant_id)
        async with get_pg() as session:
            groups, total = await community_repo.get_groups_by_merchant(
                session, mid, page, page_size
            )

            items = [GroupItemOut.model_validate(g) for g in groups]
            # Autofill joined as False or fetch if needed (usually merchant owner is automatically joined? logic TBD)

            return GroupListOut(items=items, total=total)

    async def get_groups(
        self, user_id: str | None = None, page: int = 1, page_size: int = 20
    ) -> GroupListOut:
        uid = uuid.UUID(user_id) if user_id else None
        async with get_pg() as session:
            groups, total = await community_repo.get_group_list(
                session, uid, page, page_size
            )

            items = []
            for g in groups:
                is_joined = (
                    await community_repo.check_joined(session, uid, g.id)
                    if uid
                    else False
                )
                items.append(
                    GroupItemOut(
                        id=g.id,
                        name=g.name,
                        description=g.description,
                        cover_image=g.cover_image,
                        member_count=g.member_count,
                        post_count=g.post_count,
                        is_joined=is_joined,
                        merchant_id=g.merchant_id,
                        created_at=g.created_at,
                    )
                )

            return GroupListOut(items=items, total=total)

    async def get_group_detail(
        self, group_id: str, user_id: str | None
    ) -> GroupDetailOut:
        gid = uuid.UUID(group_id)
        uid = uuid.UUID(user_id) if user_id else None

        async with get_pg() as session:
            group = await community_repo.get_group_by_id(session, gid)
            if not group:
                raise NotFoundError(COMMUNITY_GROUP_NOT_FOUND)

            is_joined = (
                await community_repo.check_joined(session, uid, gid) if uid else False
            )

            return GroupDetailOut(
                id=group.id,
                name=group.name,
                description=group.description,
                cover_image=group.cover_image,
                member_count=group.member_count,
                post_count=group.post_count,
                is_joined=is_joined,
                merchant_id=group.merchant_id,
                created_at=group.created_at,
            )

    async def join_group(self, user_id: str, group_id: str) -> None:
        uid = uuid.UUID(user_id)
        gid = uuid.UUID(group_id)
        async with get_pg() as session:
            group = await community_repo.get_group_by_id(session, gid)
            if not group:
                raise NotFoundError(COMMUNITY_GROUP_NOT_FOUND)
            await community_repo.join_group(session, uid, gid)

    async def leave_group(self, user_id: str, group_id: str) -> None:
        uid = uuid.UUID(user_id)
        gid = uuid.UUID(group_id)
        async with get_pg() as session:
            await community_repo.leave_group(session, uid, gid)

    # --- Posts ---

    async def create_post(self, user_id: str, payload: PostCreateIn) -> PostDetailOut:
        uid = uuid.UUID(user_id)
        async with get_pg() as session:
            # 确保圈子存在
            group = await community_repo.get_group_by_id(session, payload.group_id)
            if not group:
                raise NotFoundError(COMMUNITY_GROUP_NOT_FOUND)

            # 确保已加入（发帖必须先加入）
            is_joined = await community_repo.check_joined(
                session, uid, payload.group_id
            )
            if not is_joined:
                raise PermissionDeniedError("请先加入话题圈再发帖")

            post = Post(
                group_id=payload.group_id,
                user_id=uid,
                title=payload.title,
                content=payload.content,
                images=payload.images,
                videos=payload.videos,
            )
            created = await community_repo.create_post(session, post)

            # Fetch user info for return
            # Simplified: Assuming user exists if logged in
            # We can re-fetch detail or construct manually

            return PostDetailOut(
                id=created.id,
                group_id=created.group_id,
                group_name="",  # Need fetch group name? Lazy for now
                author_id=uid,
                author_name="Me",  # Placeholder, frontend usually knows
                author_avatar=None,
                title=created.title,
                content=created.content,
                images=created.images,
                videos=created.videos,
                created_at=created.created_at,
            )

    async def update_post(
        self, post_id: str, user_id: str, payload: PostUpdateIn
    ) -> PostDetailOut:
        pid = uuid.UUID(post_id)
        uid = uuid.UUID(user_id)

        async with get_pg() as session:
            # 1. Get existing post
            res = await community_repo.get_post_detail(session, pid)
            if not res:
                raise NotFoundError("Post not found")
            post, author, group = res

            # 2. Check permission
            if post.user_id != uid:
                raise PermissionDeniedError("只能编辑自己的帖子")

            # 3. Update fields
            update_data = payload.model_dump(exclude_unset=True)
            if not update_data:
                return PostDetailOut(
                    id=post.id,
                    group_id=post.group_id,
                    group_name=group.name,
                    author_id=post.user_id,
                    author_name=author.username,
                    author_avatar=author.avatar_url,
                    title=post.title,
                    content=post.content,
                    images=post.images,
                    videos=post.videos,
                    view_count=post.view_count,
                    like_count=post.likes_count,
                    comment_count=post.comment_count,
                    is_liked=False,  # Not needed for update return usually
                    is_mine=True,
                    created_at=post.created_at,
                )

            updated_post = await community_repo.update_post(session, pid, **update_data)
            if not updated_post:
                raise NotFoundError("Post not found")

            return PostDetailOut(
                id=updated_post.id,
                group_id=updated_post.group_id,
                group_name=group.name,
                author_id=updated_post.user_id,
                author_name=author.username,
                author_avatar=author.avatar_url,
                title=updated_post.title,
                content=updated_post.content,
                images=updated_post.images,
                videos=updated_post.videos,
                view_count=updated_post.view_count,
                like_count=updated_post.likes_count,
                comment_count=updated_post.comment_count,
                is_liked=False,
                is_mine=True,
                created_at=updated_post.created_at,
            )

    async def get_posts(
        self, group_id: str, user_id: str | None, page: int = 1, page_size: int = 20
    ) -> PostListOut:
        gid = uuid.UUID(group_id)
        uid = uuid.UUID(user_id) if user_id else None

        async with get_pg() as session:
            # First get group name
            group = await community_repo.get_group_by_id(session, gid)
            group_name = group.name if group else "Unknown"

            posts, total = await community_repo.get_post_list(
                session, gid, page, page_size
            )

            items = []
            for p, author in posts:
                is_liked = False
                if uid:
                    is_liked = await community_repo.check_liked(
                        session, uid, p.id, "post"
                    )

                items.append(
                    PostItemOut(
                        id=p.id,
                        group_id=p.group_id,
                        group_name=group_name,
                        author_id=p.user_id,
                        author_name=author.username,
                        author_avatar=author.avatar_url,
                        title=p.title,
                        content=p.content,
                        images=p.images,
                        videos=p.videos,
                        view_count=p.view_count,
                        like_count=p.likes_count,
                        comment_count=p.comment_count,
                        is_liked=is_liked,
                        is_mine=(uid == p.user_id),
                        is_top=p.is_top,
                        created_at=p.created_at,
                    )
                )

            return PostListOut(items=items, total=total, page=page, page_size=page_size)

    async def get_post_detail(
        self, post_id: str, user_id: str | None, ip_address: str = "unknown"
    ) -> PostDetailOut:
        pid = uuid.UUID(post_id)
        uid = uuid.UUID(user_id) if user_id else None

        async with get_pg() as session:
            res = await community_repo.get_post_detail(session, pid)
            if not res:
                raise NotFoundError("Post not found")
            post, author, group = res

            # De-duplicate View Count using Redis

            viewer_id = str(uid) if uid else f"ip_{ip_address}"
            view_key = f"viewed:post:{post_id}:{viewer_id}"

            # If lock exists (True), we skip increment. If not exists (False), we increment details.
            if not await check_operation_lock(view_key, 600):
                # Increment DB
                await community_repo.increment_view(session, pid)
                # Increment local object for return
                post.view_count += 1

            is_liked = (
                await community_repo.check_liked(session, uid, pid, "post")
                if uid
                else False
            )

            return PostDetailOut(
                id=post.id,
                group_id=post.group_id,
                group_name=group.name,
                author_id=post.user_id,
                author_name=author.username,
                author_avatar=author.avatar_url,
                title=post.title,
                content=post.content,
                images=post.images,
                videos=post.videos,
                view_count=post.view_count,
                like_count=post.likes_count,
                comment_count=post.comment_count,
                is_liked=is_liked,
                is_mine=(uid == post.user_id),
                is_top=post.is_top,
                created_at=post.created_at,
            )

    # --- Comments ---

    async def create_comment(
        self, user_id: str, post_id: str, payload: CommentCreateIn
    ) -> CommentItemOut:
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(post_id)

        async with get_pg() as session:
            # 1. Check post exists
            res = await community_repo.get_post_detail(session, pid)
            if not res:
                raise NotFoundError("Post not found")

            # 2. Get User Info for redundancy
            user = await session.get(User, uid)
            if not user:
                raise NotFoundError("User not found")

            redundant_user = CommentUserRedundancy(
                id=user.id, username=user.username, avatar=user.avatar_url
            )

            # 3. Create Mongo Comment
            from beanie import PydanticObjectId

            parent_oid = (
                PydanticObjectId(payload.parent_id) if payload.parent_id else None
            )

            comment = Comment(
                post_id=pid,
                user=redundant_user,
                content=payload.content,
                parent_id=parent_oid,
                # root_id logic is complex (needs fetch parent), skipped for MVP
            )

            created = await community_repo.create_comment(session, comment)

            return CommentItemOut(
                id=str(created.id),
                post_id=created.post_id,
                author_id=created.user.id,
                author_name=created.user.username,
                author_avatar=created.user.avatar,
                content=created.content,
                parent_id=str(created.parent_id) if created.parent_id else None,
                created_at=created.created_at,
            )

    async def get_comments(
        self, post_id: str, user_id: str | None, page: int = 1, page_size: int = 20
    ) -> CommentListOut:
        pid = uuid.UUID(post_id)
        uid = uuid.UUID(user_id) if user_id else None

        async with get_pg() as session:
            comments, total = await community_repo.get_comment_list(
                session, pid, page, page_size
            )

            items = []
            for c in comments:
                is_liked = False
                if uid:
                    is_liked = await community_repo.check_liked(
                        session, uid, str(c.id), "comment"
                    )

                items.append(
                    CommentItemOut(
                        id=str(c.id),
                        post_id=c.post_id,
                        author_id=c.user.id,
                        author_name=c.user.username,
                        author_avatar=c.user.avatar,
                        content=c.content,
                        parent_id=str(c.parent_id) if c.parent_id else None,
                        reply_to_username=c.reply_to.username if c.reply_to else None,
                        like_count=c.likes_count,  # Note: Mongo uses likes_count, Schema uses like_count
                        is_liked=is_liked,
                        created_at=c.created_at,
                    )
                )

            return CommentListOut(
                items=items, total=total, page=page, page_size=page_size
            )

    # --- Likes ---

    async def toggle_like(self, user_id: str, target_id: str, target_type: str) -> bool:
        uid = uuid.UUID(user_id)
        # target_id stays as str, allowing UUID or ObjectId
        # Repo will handle conversion
        async with get_pg() as session:
            return await community_repo.toggle_like(
                session, uid, target_id, target_type
            )

    async def moderate_post(
        self, post_id: str, is_hidden: bool, merchant_id: str
    ) -> None:
        """商家审核帖子（隐藏/显示）"""
        pid = uuid.UUID(post_id)
        mid = uuid.UUID(merchant_id)

        async with get_pg() as session:
            # 1. Get post and check ownership
            res = await community_repo.get_post_detail(session, pid)
            if not res:
                raise NotFoundError("Post not found")
            post, _, group = res

            # 2. Check if group belongs to merchant
            if group.merchant_id != mid:
                raise PermissionDeniedError("Cannot moderate posts in other groups")

            await community_repo.toggle_hide_post(session, pid, is_hidden)

    async def get_merchant_posts(
        self, merchant_id: str, page: int = 1, page_size: int = 20
    ) -> PostListOut:
        """获取商家下属圈子的所有帖子"""
        mid = uuid.UUID(merchant_id)
        async with get_pg() as session:
            posts, total = await community_repo.get_posts_by_merchant(
                session, mid, page, page_size
            )

            items = []
            for p, author, group in posts:
                items.append(
                    PostItemOut(
                        id=p.id,
                        group_id=p.group_id,
                        group_name=group.name,
                        author_id=p.user_id,
                        author_name=author.username,
                        author_avatar=author.avatar_url,
                        title=p.title,
                        content=p.content,
                        images=p.images,
                        videos=p.videos,
                        view_count=p.view_count,
                        like_count=p.likes_count,
                        comment_count=p.comment_count,
                        is_liked=False,  # Admin view, like status likely irrelevant
                        is_mine=False,
                        is_top=p.is_top,
                        is_hidden=p.is_hidden,
                        created_at=p.created_at,
                    )
                )

            return PostListOut(items=items, total=total, page=page, page_size=page_size)

    async def get_user_posts(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> PostListOut:
        """获取用户自己的帖子列表"""
        uid = uuid.UUID(user_id)
        async with get_pg() as session:
            posts, total = await community_repo.get_posts_by_user(
                session, uid, page, page_size
            )

            items = []
            for p, author, group in posts:
                is_liked = await community_repo.check_liked(session, uid, p.id, "post")
                items.append(
                    PostItemOut(
                        id=p.id,
                        group_id=p.group_id,
                        group_name=group.name,
                        author_id=p.user_id,
                        author_name=author.username,
                        author_avatar=author.avatar_url,
                        title=p.title,
                        content=p.content,
                        images=p.images,
                        videos=p.videos,
                        view_count=p.view_count,
                        like_count=p.likes_count,
                        comment_count=p.comment_count,
                        is_liked=is_liked,
                        is_mine=True,
                        is_top=p.is_top,
                        is_hidden=p.is_hidden,
                        created_at=p.created_at,
                    )
                )

            return PostListOut(items=items, total=total, page=page, page_size=page_size)

    async def search_posts(
        self, query: str, user_id: str | None = None, page: int = 1, page_size: int = 20
    ) -> PostListOut:
        """全局搜索帖子"""
        uid = uuid.UUID(user_id) if user_id else None
        async with get_pg() as session:
            posts, total = await community_repo.search_posts(
                session, query, page, page_size
            )

            items = []
            for p, author, group in posts:
                is_liked = (
                    await community_repo.check_liked(session, uid, p.id, "post")
                    if uid
                    else False
                )
                items.append(
                    PostItemOut(
                        id=p.id,
                        group_id=p.group_id,
                        group_name=group.name,
                        author_id=p.user_id,
                        author_name=author.username,
                        author_avatar=author.avatar_url,
                        title=p.title,
                        content=p.content,
                        images=p.images,
                        videos=p.videos,
                        view_count=p.view_count,
                        like_count=p.likes_count,
                        comment_count=p.comment_count,
                        is_liked=is_liked,
                        is_mine=(uid == p.user_id),
                        is_top=p.is_top,
                        is_hidden=p.is_hidden,
                        created_at=p.created_at,
                    )
                )

            return PostListOut(items=items, total=total, page=page, page_size=page_size)
