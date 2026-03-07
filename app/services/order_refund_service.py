"""退款服务层"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import BackgroundTasks

from app.common.errors import BusinessError, NotFoundError
from app.database.pgsql import get_pg
from app.entity.pgsql import OrderRefund
from app.repo import (
    merchants_repo,
    orders_repo,
    products_repo,
)
from app.repo.order_refunds_repo import order_refunds_repo
from app.schemas.order_refund import (
    OrderRefundApplyIn,
    OrderRefundAuditIn,
    OrderRefundOut,
)
from app.services.notification_service import notification_service


class OrderRefundService:
    """退款与售后服务"""

    async def apply_refund(
        self, user_id: str, order_id: str, payload: OrderRefundApplyIn
    ) -> OrderRefundOut:
        """用户申请退款"""
        async with get_pg() as session:
            order = await orders_repo.get_by_id(session, order_id)
            if not order or str(order.user_id) != user_id:
                raise NotFoundError("订单不存在")

            # 只能在已支付、已发货、已完成状态下申请
            if order.status not in ("paid", "shipped", "completed"):
                raise BusinessError(detail="当前订单状态不可申请退款")

            # 检查是否已有退款记录且未被拒绝
            existing_refund = await order_refunds_repo.get_by_order_id(
                session, str(order.id)
            )
            if existing_refund and existing_refund.status in ("pending", "approved"):
                raise BusinessError(detail="该订单已存在退款申请")

            # 创建退款单
            refund = OrderRefund(
                order_id=order.id,
                user_id=uuid.UUID(user_id),
                reason=payload.reason,
                amount=order.total_amount,
                status="pending",
            )
            await order_refunds_repo.create(session, refund)

            # 更新订单状态和退款标记
            order.status = "refunding"
            order.refund_status = "pending"
            await session.flush()

            return OrderRefundOut.model_validate(refund)

    async def get_refund_detail(self, user_id: str, order_id: str) -> OrderRefundOut:
        """获取退款详情 (允许买家或关联商家访问)"""
        async with get_pg() as session:
            # 1. 获取退款单
            refund = await order_refunds_repo.get_by_order_id(session, order_id)
            if not refund:
                raise NotFoundError("退款记录不存在")

            # 2. 权限检查
            # a. 如果是买家本人
            if str(refund.user_id) == user_id:
                return OrderRefundOut.model_validate(refund)

            # b. 如果是商户，检查是否为订单中商品的商户
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if merchant:
                items = await orders_repo.get_items_by_order_id(
                    session, uuid.UUID(order_id)
                )
                if items:
                    product = await products_repo.get_by_id(
                        session, str(items[0].product_id)
                    )
                    if product and product.merchant_id == merchant.id:
                        return OrderRefundOut.model_validate(refund)

            # 3. 否则无权访问
            raise NotFoundError("订单不存在")

    async def audit_refund(
        self,
        merchant_user_id: str,
        refund_id: str,
        payload: OrderRefundAuditIn,
        background_tasks: BackgroundTasks,
    ) -> OrderRefundOut:
        """商家审核退款"""
        async with get_pg() as session:
            # 1. 验证商家身份
            merchant = await merchants_repo.get_by_user_id(session, merchant_user_id)
            if not merchant:
                raise BusinessError(detail="当前用户非商家")

            # 2. 获取退款单
            refund = await order_refunds_repo.get_by_id(session, refund_id)
            if not refund:
                raise NotFoundError("退款单不存在")

            if refund.status != "pending":
                raise BusinessError(detail="退款单已处理")

            # 3. 验证订单及归属
            order = await orders_repo.get_by_id(session, str(refund.order_id))
            if not order:
                raise NotFoundError("关联订单缺失")

            # （由于当前系统没做 order 与 merchant 的直接外键，需通过 order_items 的商品找 merchant）
            # 简单验证商家的权限
            items = await orders_repo.get_items_by_order_id(session, order.id)
            if not items:
                raise BusinessError(detail="订单明细异常")
            product = await products_repo.get_by_id(session, str(items[0].product_id))
            if not product or product.merchant_id != merchant.id:
                raise BusinessError(detail="无权操作此订单的退款")

            # 4. 执行同意或拒绝
            refund.status = payload.status
            refund.merchant_reply = payload.merchant_reply
            refund.updated_at = datetime.now(UTC)

            if payload.status == "approved":
                # 同意退款
                refund.status = "approved"
                order.status = "refunded"
                order.refund_status = "approved"
                # 归还库存，扣减销量 (如果支付时加了销量的话)
                for item in items:
                    await products_repo.recover_stock(
                        session, item.product_id, item.quantity
                    )
                    # 假定此处允许销量扣减
                    p = await products_repo.get_by_id(session, str(item.product_id))
                    if p and p.sales_count >= item.quantity:
                        p.sales_count -= item.quantity

                # 归还积分 (如果使用了积分抵扣)
                if order.points_consumed and order.points_consumed > 0:
                    from app.services.point_service import point_service

                    await point_service.grant_points(
                        session,
                        order.user_id,
                        order.points_consumed,
                        reason=f"订单退款返还积分: {order.order_no}",
                        related_id=str(order.id),
                    )

                # 2. 扣回奖励积分 (支付时发放的部分)
                from app.services.point_service import point_service

                base_amount = order.total_amount + (order.coupon_amount or Decimal("0"))
                points_to_clawback = base_amount / Decimal("10")
                if points_to_clawback > 0:
                    await point_service.consume_points(
                        session,
                        order.user_id,
                        points_to_clawback,
                        reason=f"订单退款扣回奖励积分: {order.order_no}",
                        related_id=str(order.id),
                        allow_negative=True,
                    )

                # 3. 回滚成长值 (累计消费)
                await point_service.update_growth(session, order.user_id, -base_amount)

                from app.database.redis import get_redis
                from app.services.redis_stock_service import redis_stock_service

                async with get_redis() as redis_client:
                    for item in items:
                        await redis_stock_service.release(
                            redis_client, session, item.product_id, item.quantity
                        )

                # 4. 发送通知
                background_tasks.add_task(
                    notification_service.create_notification,
                    str(order.user_id),
                    "order",
                    "退款申请已通过",
                    f"您的订单 {order.order_no} 退款审核已通过，退款即将原路返回。",
                    f"/member/orders/{order.id}",
                )
            else:
                # 拒绝退款 -> 恢复到原状态，但标记为已打回
                refund.status = "rejected"
                order.refund_status = "rejected"

                if order.completed_at:
                    order.status = "completed"
                elif order.shipped_at:
                    order.status = "shipped"
                else:
                    order.status = "paid"

                # 5. 发送拒绝退款通知
                background_tasks.add_task(
                    notification_service.create_notification,
                    str(order.user_id),
                    "order",
                    "退款申请被驳回",
                    f"您的订单 {order.order_no} 退款申请已被驳回。商家回复：{payload.merchant_reply or '无'}",
                    f"/member/orders/{order.id}",
                )

            await session.flush()
            return OrderRefundOut.model_validate(refund)

    async def get_merchant_refunds(
        self,
        merchant_user_id: str,
        page: int = 1,
        page_size: int = 10,
        status: str | None = None,
    ) -> tuple[list[OrderRefundOut], int]:
        """获取商家的退款/售后列表"""
        async with get_pg() as session:
            merchant = await merchants_repo.get_by_user_id(session, merchant_user_id)
            if not merchant:
                raise BusinessError(detail="当前用户非商家")

            refunds, total = await order_refunds_repo.get_list_by_merchant(
                session, str(merchant.id), page, page_size, status
            )

            return [OrderRefundOut.model_validate(r) for r in refunds], total


order_refund_service = OrderRefundService()
