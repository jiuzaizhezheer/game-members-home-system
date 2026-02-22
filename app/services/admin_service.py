"""管理员业务逻辑层"""

import uuid

from app.common.constants import MERCHANT_NOT_FOUND, PRODUCT_NOT_FOUND, USER_NOT_FOUND
from app.common.errors import NotFoundError
from app.database.pgsql import get_pg
from app.repo import (
    admin_community_repo,
    admin_log_repo,
    admin_products_repo,
    admin_stats_repo,
    admin_users_repo,
    community_repo,
)
from app.schemas.admin import (
    AdminDashboardOut,
    AdminMerchantItemOut,
    AdminMerchantListOut,
    AdminUserItemOut,
    AdminUserListOut,
)
from app.schemas.community import CommentItemOut, CommentListOut, PostListOut
from app.schemas.order import OrderItemOut, OrderListOut, OrderOut
from app.schemas.product import ProductListOut, ProductOut


class AdminService:
    """管理员服务"""

    # --- 仪表盘 ---

    async def get_dashboard_stats(self) -> AdminDashboardOut:
        """获取管理后台仪表盘统计数据"""
        async with get_pg() as session:
            data = await admin_stats_repo.get_platform_stats(session)
            return AdminDashboardOut.model_validate(data)

    # --- 用户管理 ---

    async def get_users(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> AdminUserListOut:
        """获取用户列表"""
        async with get_pg() as session:
            users, total = await admin_users_repo.get_user_list(
                session,
                page=page,
                page_size=page_size,
                keyword=keyword,
                role=role,
                is_active=is_active,
            )
            items = [AdminUserItemOut.model_validate(u) for u in users]
            return AdminUserListOut(
                items=items, total=total, page=page, page_size=page_size
            )

    async def get_user_detail(self, user_id: str) -> AdminUserItemOut:
        """获取用户详情"""
        async with get_pg() as session:
            user = await admin_users_repo.get_user_by_id(session, user_id)
            if not user:
                raise NotFoundError(USER_NOT_FOUND)
            return AdminUserItemOut.model_validate(user)

    async def disable_user(self, user_id: str, admin_id: str) -> None:
        """禁用用户"""
        admin_uuid = uuid.UUID(admin_id)
        async with get_pg() as session:
            user = await admin_users_repo.get_user_by_id(session, user_id)
            if not user:
                raise NotFoundError(USER_NOT_FOUND)
            await admin_users_repo.set_user_active(session, user_id, False)
            await admin_log_repo.create_log(
                session,
                admin_id=admin_uuid,
                action="disable_user",
                target_type="user",
                target_id=user_id,
                detail={"username": user.username},
            )

    async def enable_user(self, user_id: str, admin_id: str) -> None:
        """启用用户"""
        admin_uuid = uuid.UUID(admin_id)
        async with get_pg() as session:
            user = await admin_users_repo.get_user_by_id(session, user_id)
            if not user:
                raise NotFoundError(USER_NOT_FOUND)
            await admin_users_repo.set_user_active(session, user_id, True)
            await admin_log_repo.create_log(
                session,
                admin_id=admin_uuid,
                action="enable_user",
                target_type="user",
                target_id=user_id,
                detail={"username": user.username},
            )

    # --- 商家管理 ---

    async def get_merchants(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
    ) -> AdminMerchantListOut:
        """获取商家列表"""
        async with get_pg() as session:
            rows, total = await admin_users_repo.get_merchant_list(
                session, page=page, page_size=page_size, keyword=keyword
            )
            items = [
                AdminMerchantItemOut(
                    user_id=row["user"].id,
                    username=row["user"].username,
                    email=row["user"].email,
                    is_active=row["user"].is_active,
                    merchant_id=row["merchant"].id,
                    shop_name=row["merchant"].shop_name,
                    contact_phone=row["merchant"].contact_phone,
                    shop_desc=row["merchant"].shop_desc,
                    logo_url=row["merchant"].logo_url,
                    created_at=row["merchant"].created_at,
                )
                for row in rows
            ]
            return AdminMerchantListOut(
                items=items, total=total, page=page, page_size=page_size
            )

    async def get_merchant_detail(self, merchant_id: str) -> AdminMerchantItemOut:
        """获取商家详情"""
        async with get_pg() as session:
            row = await admin_users_repo.get_merchant_detail(session, merchant_id)
            if not row:
                raise NotFoundError(MERCHANT_NOT_FOUND)
            return AdminMerchantItemOut(
                user_id=row["user"].id,
                username=row["user"].username,
                email=row["user"].email,
                is_active=row["user"].is_active,
                merchant_id=row["merchant"].id,
                shop_name=row["merchant"].shop_name,
                contact_phone=row["merchant"].contact_phone,
                shop_desc=row["merchant"].shop_desc,
                logo_url=row["merchant"].logo_url,
                created_at=row["merchant"].created_at,
            )

    async def verify_merchant(
        self, merchant_id: str, is_active: bool, admin_id: str
    ) -> None:
        """审核商家（启用/禁用商家账号）"""
        admin_uuid = uuid.UUID(admin_id)
        async with get_pg() as session:
            ok = await admin_users_repo.set_merchant_active(
                session, merchant_id, is_active
            )
            if not ok:
                raise NotFoundError(MERCHANT_NOT_FOUND)
            await admin_log_repo.create_log(
                session,
                admin_id=admin_uuid,
                action="verify_merchant",
                target_type="merchant",
                target_id=merchant_id,
                detail={"is_active": is_active},
            )

    # --- 商品管理 ---

    async def get_all_products(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        status: str | None = None,
    ) -> ProductListOut:
        """获取全平台商品列表"""
        async with get_pg() as session:
            products, total = await admin_products_repo.get_all_products(
                session, page=page, page_size=page_size, keyword=keyword, status=status
            )
            items = [ProductOut.model_validate(p) for p in products]
            return ProductListOut(
                items=items, total=total, page=page, page_size=page_size
            )

    async def get_product_detail(self, product_id: str) -> ProductOut:
        """获取商品详情"""
        async with get_pg() as session:
            product = await admin_products_repo.get_product_by_id(session, product_id)
            if not product:
                raise NotFoundError(PRODUCT_NOT_FOUND)
            return ProductOut.model_validate(product)

    async def force_offline_product(self, product_id: str, admin_id: str) -> None:
        """强制下架商品"""
        admin_uuid = uuid.UUID(admin_id)
        async with get_pg() as session:
            product = await admin_products_repo.get_product_by_id(session, product_id)
            if not product:
                raise NotFoundError(PRODUCT_NOT_FOUND)
            await admin_products_repo.force_offline_product(session, product_id)
            await admin_log_repo.create_log(
                session,
                admin_id=admin_uuid,
                action="force_offline_product",
                target_type="product",
                target_id=product_id,
                detail={"product_name": product.name},
            )

    # --- 订单管理 ---

    async def get_all_orders(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> OrderListOut:
        """获取全平台订单列表"""
        async with get_pg() as session:
            orders, total = await admin_products_repo.get_all_orders(
                session, page=page, page_size=page_size, status=status
            )
            ordered_out = []
            for o in orders:
                items = await admin_products_repo.get_items_by_order_id(session, o.id)
                o_out = OrderOut.model_validate(o)
                o_out.items = [
                    OrderItemOut(
                        id=i.id,
                        product_id=i.product_id,
                        quantity=i.quantity,
                        unit_price=i.unit_price,
                        product_name=i.product.name,
                        product_image=i.product.image_url,
                    )
                    for i in items
                ]
                ordered_out.append(o_out)
            return OrderListOut(
                items=ordered_out, total=total, page=page, page_size=page_size
            )

    async def get_order_detail(self, order_id: str) -> OrderOut:
        """获取订单详情"""
        async with get_pg() as session:
            order = await admin_products_repo.get_order_by_id(session, order_id)
            if not order:
                raise NotFoundError("订单不存在")
            items = await admin_products_repo.get_items_by_order_id(session, order.id)
            out = OrderOut.model_validate(order)
            out.items = [
                OrderItemOut(
                    id=i.id,
                    product_id=i.product_id,
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                    product_name=i.product.name,
                    product_image=i.product.image_url,
                )
                for i in items
            ]
            return out

    # --- 社区内容审核 ---

    async def get_all_posts(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        is_hidden: bool | None = None,
    ) -> PostListOut:
        """获取全平台帖子列表"""
        from app.repo import admin_community_repo
        from app.schemas.community import PostItemOut, PostListOut

        async with get_pg() as session:
            posts, total = await admin_community_repo.get_all_posts(
                session,
                page=page,
                page_size=page_size,
                keyword=keyword,
                is_hidden=is_hidden,
            )
            items = [
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
                    is_top=p.is_top,
                    is_hidden=p.is_hidden,
                    created_at=p.created_at,
                )
                for p, author, group in posts
            ]
            return PostListOut(items=items, total=total, page=page, page_size=page_size)

    async def review_post(self, post_id: str, is_hidden: bool, admin_id: str) -> None:
        """审核帖子（隐藏/显示）"""
        admin_uuid = uuid.UUID(admin_id)
        post_uuid = uuid.UUID(post_id)
        async with get_pg() as session:
            result = await community_repo.toggle_hide_post(
                session, post_uuid, is_hidden
            )
            if not result:
                raise NotFoundError("帖子不存在")
            await admin_log_repo.create_log(
                session,
                admin_id=admin_uuid,
                action="review_post",
                target_type="post",
                target_id=post_id,
                detail={"is_hidden": is_hidden},
            )

    async def delete_post(self, post_id: str, admin_id: str) -> None:
        """删除帖子"""
        admin_uuid = uuid.UUID(admin_id)
        post_uuid = uuid.UUID(post_id)
        async with get_pg() as session:
            await community_repo.delete_post(session, post_uuid)
            await admin_log_repo.create_log(
                session,
                admin_id=admin_uuid,
                action="delete_post",
                target_type="post",
                target_id=post_id,
            )

    async def get_all_comments(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        post_id: str | None = None,
    ) -> CommentListOut:
        """获取全平台评论列表"""
        comments, total = await admin_community_repo.get_all_comments(
            page=page, page_size=page_size, post_id=post_id
        )
        items = [
            CommentItemOut(
                id=str(c.id),
                post_id=c.post_id,
                author_id=c.user.id,
                author_name=c.user.username,
                author_avatar=c.user.avatar,
                content=c.content,
                parent_id=str(c.parent_id) if c.parent_id else None,
                like_count=c.likes_count,
                created_at=c.created_at,
            )
            for c in comments
        ]
        return CommentListOut(items=items, total=total, page=page, page_size=page_size)

    async def delete_comment(self, comment_id: str, admin_id: str) -> None:
        """删除评论"""
        admin_uuid = uuid.UUID(admin_id)
        deleted = await admin_community_repo.delete_comment(comment_id)
        if not deleted:
            raise NotFoundError("评论不存在")
        # 评论存于 MongoDB，日志写入 PostgreSQL（独立连接）
        async with get_pg() as session:
            await admin_log_repo.create_log(
                session,
                admin_id=admin_uuid,
                action="delete_comment",
                target_type="comment",
                target_id=comment_id,
            )
