"""订单服务层：订单业务逻辑"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import BackgroundTasks

from app.common.constants import ORDER_STATUS_ERROR
from app.common.errors import BusinessError, NotFoundError
from app.database.pgsql import get_pg
from app.entity.pgsql import Order, OrderItem
from app.repo import (
    addresses_repo,
    carts_repo,
    merchants_repo,
    orders_repo,
    products_repo,
)
from app.schemas.order import (
    BuyNowIn,
    OrderCreateIn,
    OrderItemOut,
    OrderOut,
    OrderShipIn,
)
from app.utils import generate_order_no


class OrderService:
    """订单服务"""

    async def create_from_cart(self, user_id: str, payload: OrderCreateIn) -> OrderOut:
        """从购物车创建订单"""
        async with get_pg() as session:
            # 1. 验证地址
            address = await addresses_repo.get_by_id(session, str(payload.address_id))
            if not address or str(address.user_id) != user_id:
                raise NotFoundError("收货地址不存在")

            # 2. 获取当前的活动购物车及明细
            cart = await carts_repo.get_active_by_user_id(session, user_id)
            if not cart:
                raise BusinessError(detail="购物车为空")

            cart_items = await carts_repo.get_items(session, cart.id)
            if not cart_items:
                raise BusinessError(detail="购物车没有商品")

            # ... (中间计费和扣库存逻辑保持不变) ...
            # 3. 计算总价并扣减库存
            total_amount = Decimal("0.00")
            order_items_to_create = []

            # 获取所有商品的有效促销
            from app.services.promotion_service import PromotionService

            promotion_service = PromotionService()
            product_ids = [ci.product_id for ci in cart_items]
            active_promotions = (
                await promotion_service.get_active_promotions_by_product_ids(
                    product_ids
                )
            )

            # 为了防止并发问题，我们在 products_repo 中使用了 FOR UPDATE
            for ci in cart_items:
                # 获取该商品的最新价格 (通常下单时锁定价格)
                product = await products_repo.get_by_id(session, str(ci.product_id))
                if not product or product.status != "on":
                    raise BusinessError(detail=f"商品 {ci.product_id} 已下架或不存在")

                # 扣减库存
                success = await products_repo.deduct_stock(
                    session, ci.product_id, ci.quantity
                )
                if not success:
                    raise BusinessError(detail=f"商品 {product.name} 库存不足")

                # 计算价格 (应用促销)
                product_price = Decimal(str(product.price))
                unit_price = product_price
                if product.id in active_promotions:
                    promo = active_promotions[product.id]
                    discount_value = Decimal(str(promo.discount_value))
                    if promo.discount_type == "percent":
                        # discount_value=20 means 20% OFF -> 80% price
                        # discount_value=20 means 80%? No, usually 20 means 20% OFF.
                        # Wait, in create.tsx: "输入 20 代表 20% OFF (即8折)"
                        # So multiplier is (100 - 20) / 100 = 0.8
                        discount_rate = (Decimal(100) - discount_value) / Decimal(100)
                        # Ensure non-negative
                        discount_rate = max(discount_rate, Decimal(0))
                        unit_price = product_price * discount_rate
                    elif promo.discount_type == "fixed":
                        unit_price = product_price - discount_value
                        unit_price = max(unit_price, Decimal("0.01"))  # At least 0.01

                # 计算小计
                subtotal = unit_price * ci.quantity
                total_amount += subtotal

                # 准备订单明细
                order_items_to_create.append(
                    OrderItem(
                        product_id=ci.product_id,
                        quantity=ci.quantity,
                        unit_price=unit_price,  # Store the actual (discounted) price
                        product=product,  # 赋值以便下文直接获取名称
                    )
                )

            # 3.5 优惠券核销
            user_coupon_id = payload.user_coupon_id
            coupon_amount = Decimal("0.00")
            if user_coupon_id:
                from app.repo import coupons_repo
                from app.services.coupon_service import CouponService

                coupon_service = CouponService()

                # 获取商家ID集合用于校验商家券
                merchant_ids = {
                    item.product.merchant_id for item in order_items_to_create
                }

                user_coupon, coupon = await coupon_service.validate_coupon_for_order(
                    uuid.UUID(user_id), user_coupon_id, total_amount, merchant_ids
                )

                # 计算优惠金额
                if coupon.discount_type == "percent":
                    coupon_amount = total_amount * (
                        Decimal(str(coupon.discount_value)) / Decimal(100)
                    )
                else:
                    coupon_amount = Decimal(str(coupon.discount_value))

                # 确保折扣不超过总价
                coupon_amount = min(coupon_amount, total_amount)
                total_amount -= coupon_amount

            # 3.6 积分抵扣
            point_deduction_amount = Decimal("0.00")
            points_consumed = Decimal("0.00")
            if payload.use_points:
                from app.repo import users_repo
                from app.services.point_service import point_service

                user = await users_repo.get_by_id(session, str(user_id))
                if user and user.points > 0:
                    # 计算最大可抵扣
                    max_deduction, max_points = (
                        point_service.calculate_points_deduction(
                            user.points, total_amount
                        )
                    )

                    if payload.points_to_use is not None:
                        # 使用用户指定的积分，但不超过最大可抵扣和用户余额
                        actual_points = min(
                            payload.points_to_use, max_points, user.points
                        )
                        points_consumed = actual_points
                        point_deduction_amount = (
                            points_consumed
                            / Decimal(str(point_service.POINTS_TO_CASH_RATIO))
                        ).quantize(Decimal("0.01"))
                    else:
                        point_deduction_amount = max_deduction
                        points_consumed = max_points

                    total_amount -= point_deduction_amount

            # 4. 创建订单记录
            new_order = Order(
                user_id=uuid.UUID(user_id),
                address_id=payload.address_id,
                order_no=generate_order_no(),
                status="pending",
                total_amount=total_amount,
                user_coupon_id=user_coupon_id,
                coupon_amount=coupon_amount if user_coupon_id else None,
                point_deduction_amount=(
                    point_deduction_amount if point_deduction_amount > 0 else None
                ),
                points_consumed=points_consumed if points_consumed > 0 else None,
            )
            await orders_repo.create(session, new_order)

            # 4.5 标记优惠券使用
            if user_coupon_id:
                from app.repo import coupons_repo

                await coupons_repo.use_user_coupon(
                    session, user_coupon_id, new_order.id
                )

            # 5. 关联订单明细并保存
            for item in order_items_to_create:
                item.order_id = new_order.id
            await orders_repo.add_items(session, order_items_to_create)

            # 6. 标记购物车为已结算 (而不是仅仅清空项目)
            cart.is_checked_out = True
            await session.flush()

            # 7. 组装响应
            return OrderOut(
                id=new_order.id,
                order_no=new_order.order_no,
                status=new_order.status,
                total_amount=new_order.total_amount,
                address_id=new_order.address_id,
                created_at=new_order.created_at,
                user_coupon_id=new_order.user_coupon_id,
                coupon_amount=new_order.coupon_amount,
                refund_status=None,
                items=[
                    OrderItemOut(
                        id=oi.id,
                        product_id=oi.product_id,
                        quantity=oi.quantity,
                        unit_price=oi.unit_price,
                        product_name=oi.product.name,
                        product_image=oi.product.image_url,
                        is_reviewed=False,  # 新订单肯定未评价
                    )
                    for oi in order_items_to_create
                ],
            )

    async def buy_now(self, user_id: str, payload: BuyNowIn) -> OrderOut:
        """立即购买：绕过购物车直接创建订单"""
        async with get_pg() as session:
            # 1. 验证地址
            address = await addresses_repo.get_by_id(session, str(payload.address_id))
            if not address or str(address.user_id) != user_id:
                raise NotFoundError("收货地址不存在")

            # 2. 验证商品
            product = await products_repo.get_by_id(session, str(payload.product_id))
            if not product or product.status != "on":
                raise BusinessError(detail="商品已下架或不存在")

            # 3. 扣减库存
            success = await products_repo.deduct_stock(
                session, payload.product_id, payload.quantity
            )
            if not success:
                raise BusinessError(detail=f"商品 {product.name} 库存不足")

            # 4. 计算总价 (应用促销)
            from app.services.promotion_service import PromotionService

            promotion_service = PromotionService()
            active_promotions = (
                await promotion_service.get_active_promotions_by_product_ids(
                    [product.id]
                )
            )

            product_price = Decimal(str(product.price))
            unit_price = product_price
            if product.id in active_promotions:
                promo = active_promotions[product.id]
                discount_value = Decimal(str(promo.discount_value))
                if promo.discount_type == "percent":
                    discount_rate = (Decimal(100) - discount_value) / Decimal(100)
                    discount_rate = max(discount_rate, Decimal(0))
                    unit_price = product_price * discount_rate
                elif promo.discount_type == "fixed":
                    unit_price = product_price - discount_value
                    unit_price = max(unit_price, Decimal("0.01"))

            total_amount = unit_price * payload.quantity

            # 4.5 优惠券核销
            user_coupon_id = payload.user_coupon_id
            coupon_amount = Decimal("0.00")
            if user_coupon_id:
                from app.services.coupon_service import CouponService

                coupon_service = CouponService()

                user_coupon, coupon = await coupon_service.validate_coupon_for_order(
                    uuid.UUID(user_id),
                    user_coupon_id,
                    total_amount,
                    {product.merchant_id},
                )

                # 计算优惠金额
                if coupon.discount_type == "percent":
                    coupon_amount = total_amount * (
                        Decimal(str(coupon.discount_value)) / Decimal(100)
                    )
                else:
                    coupon_amount = Decimal(str(coupon.discount_value))

                # 确保折扣不超过总价
                coupon_amount = min(coupon_amount, total_amount)
                total_amount -= coupon_amount

            # 4.6 积分抵扣
            point_deduction_amount = Decimal("0.00")
            points_consumed = Decimal("0.00")
            if payload.use_points:
                from app.repo import users_repo
                from app.services.point_service import point_service

                user = await users_repo.get_by_id(session, str(user_id))
                if user and user.points > 0:
                    # 计算最大可抵扣
                    max_deduction, max_points = (
                        point_service.calculate_points_deduction(
                            user.points, total_amount
                        )
                    )

                    if payload.points_to_use is not None:
                        # 使用用户指定的积分，但不超过最大可抵扣和用户余额
                        actual_points = min(
                            payload.points_to_use, max_points, user.points
                        )
                        points_consumed = actual_points
                        point_deduction_amount = (
                            points_consumed
                            / Decimal(str(point_service.POINTS_TO_CASH_RATIO))
                        ).quantize(Decimal("0.01"))
                    else:
                        point_deduction_amount = max_deduction
                        points_consumed = max_points

                    total_amount -= point_deduction_amount

            # 5. 创建订单
            new_order = Order(
                user_id=uuid.UUID(user_id),
                address_id=payload.address_id,
                order_no=generate_order_no(),
                status="pending",
                total_amount=total_amount,
                user_coupon_id=user_coupon_id,
                coupon_amount=coupon_amount if user_coupon_id else None,
                point_deduction_amount=(
                    point_deduction_amount if point_deduction_amount > 0 else None
                ),
                points_consumed=points_consumed if points_consumed > 0 else None,
            )
            await orders_repo.create(session, new_order)

            # 5.5 标记优惠券使用
            if user_coupon_id:
                from app.repo import coupons_repo

                await coupons_repo.use_user_coupon(
                    session, user_coupon_id, new_order.id
                )

            # 6. 创建订单明细
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=payload.product_id,
                quantity=payload.quantity,
                unit_price=unit_price,
                product=product,
            )
            await orders_repo.add_items(session, [order_item])

            # 7. 组装响应
            return OrderOut(
                id=new_order.id,
                order_no=new_order.order_no,
                status=new_order.status,
                total_amount=new_order.total_amount,
                address_id=new_order.address_id,
                created_at=new_order.created_at,
                user_coupon_id=new_order.user_coupon_id,
                coupon_amount=new_order.coupon_amount,
                refund_status=None,
                items=[
                    OrderItemOut(
                        id=order_item.id,
                        product_id=order_item.product_id,
                        quantity=order_item.quantity,
                        unit_price=order_item.unit_price,
                        product_name=product.name,
                        product_image=product.image_url,
                        is_reviewed=False,
                    )
                ],
            )

    async def get_my_orders(
        self, user_id: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[OrderOut], int]:
        """获取我的订单列表"""
        async with get_pg() as session:
            orders, total = await orders_repo.get_list_by_user(
                session, user_id, page, page_size
            )

            ordered_out = []
            from app.repo.reviews_repo import reviews_repo

            for o in orders:
                items = await orders_repo.get_items_by_order_id(session, o.id)
                o_out = OrderOut.model_validate(o)
                oi_list = []
                for i in items:
                    is_reviewed = False
                    if o.status == "completed":
                        r = await reviews_repo.get_by_order_item(
                            str(o.id), str(i.product_id)
                        )
                        is_reviewed = r is not None

                    oi_list.append(
                        OrderItemOut(
                            id=i.id,
                            product_id=i.product_id,
                            quantity=i.quantity,
                            unit_price=i.unit_price,
                            product_name=i.product.name,
                            product_image=i.product.image_url,
                            is_reviewed=is_reviewed,
                        )
                    )
                o_out.items = oi_list
                ordered_out.append(o_out)

            return ordered_out, total

    async def get_order_detail(self, user_id: str, order_id: str) -> OrderOut:
        """获取订单详情"""
        async with get_pg() as session:
            order = await orders_repo.get_by_id(session, order_id)
            if not order or str(order.user_id) != user_id:
                raise NotFoundError("订单不存在")

            items = await orders_repo.get_items_by_order_id(session, order.id)
            out = OrderOut.model_validate(order)

            from app.repo.reviews_repo import reviews_repo

            oi_list = []
            for i in items:
                is_reviewed = False
                if order.status == "completed":
                    r = await reviews_repo.get_by_order_item(
                        str(order.id), str(i.product_id)
                    )
                    is_reviewed = r is not None

                oi_list.append(
                    OrderItemOut(
                        id=i.id,
                        product_id=i.product_id,
                        quantity=i.quantity,
                        unit_price=i.unit_price,
                        product_name=i.product.name,
                        product_image=i.product.image_url,
                        is_reviewed=is_reviewed,
                    )
                )
            out.items = oi_list
            return out

    async def cancel_order(self, user_id: str, order_id: str) -> None:
        """取消订单"""
        async with get_pg() as session:
            # 1. 获取订单
            order = await orders_repo.get_by_id(session, order_id)
            if not order or str(order.user_id) != user_id:
                raise NotFoundError("订单不存在")

            # 2. 状态校验
            if order.status != "pending":
                raise BusinessError(detail=ORDER_STATUS_ERROR)

            # 3. 归还库存
            items = await orders_repo.get_items_by_order_id(session, order.id)
            for item in items:
                await products_repo.recover_stock(
                    session, item.product_id, item.quantity
                )

            # 4. 更新状态
            order.status = "cancelled"
            await session.flush()

    async def pay_order(self, user_id: str, order_id: str) -> None:
        """模拟支付订单"""
        async with get_pg() as session:
            # 1. 获取订单
            order = await orders_repo.get_by_id(session, order_id)
            if not order or str(order.user_id) != user_id:
                raise NotFoundError("订单不存在")

            # 2. 状态校验
            if order.status != "pending":
                raise BusinessError(detail="订单状态不可支付")

            # 3. 更新销量与人气分
            items = await orders_repo.get_items_by_order_id(session, order.id)
            for item in items:
                await products_repo.increment_sales(
                    session, item.product_id, item.quantity
                )

            # 4. 执行积分扣减 (如果使用了积分抵扣)
            if order.points_consumed and order.points_consumed > 0:
                from app.services.point_service import point_service

                await point_service.consume_points(
                    session,
                    order.user_id,
                    order.points_consumed,
                    reason=f"订单支付抵扣: {order.order_no}",
                    related_id=str(order.id),
                )

            # 5. 更新状态为已支付
            order.status = "paid"
            order.paid_at = datetime.now(UTC)
            await session.flush()

            # 5. 会员积分与成长值
            from app.services.point_service import point_service

            # 按优惠前总金额 (实付 + 优惠券) 10:1 发放积分
            base_amount = order.total_amount + (order.coupon_amount or Decimal("0"))
            points_to_grant = base_amount / Decimal("10")
            if points_to_grant > 0:
                await point_service.grant_points(
                    session,
                    order.user_id,
                    points_to_grant,
                    "订单支付奖励",
                    related_id=str(order.id),
                )
            # 更新成长值并晋升等级
            await point_service.update_growth(session, order.user_id, base_amount)

    async def ship_order(
        self, order_id: str, payload: OrderShipIn, background_tasks: BackgroundTasks
    ) -> None:
        """订单发货"""
        async with get_pg() as session:
            order = await orders_repo.get_by_id(session, order_id)
            if not order:
                raise NotFoundError("订单不存在")

            if order.status != "paid":
                # 暂时严格校验必须支付后发货
                raise BusinessError(detail="订单未支付或状态异常")

            order.status = "shipped"
            order.shipped_at = datetime.now(UTC)
            order.courier_name = payload.courier_name
            order.tracking_no = payload.tracking_no
            await session.flush()

            # 触发后台真实物流模拟
            from app.services.logistics_service import logistics_service

            # 1. 立即记录起点
            await logistics_service.add_initial_log(
                order_id=order.id,
                courier_name=payload.courier_name,
                tracking_no=payload.tracking_no,
                location=payload.sender_address,
            )
            if order.address_id is None:
                raise BusinessError(detail="订单缺少收货地址")
            # 2. 调度后台任务模拟后续状态
            background_tasks.add_task(
                logistics_service.simulate_shipping_progress,
                order_id=order.id,
                address_id=order.address_id,
            )

    async def receipt_order(self, user_id: str, order_id: str) -> None:
        """确认收货"""
        async with get_pg() as session:
            order = await orders_repo.get_by_id(session, order_id)
            if not order or str(order.user_id) != user_id:
                raise NotFoundError("订单不存在")

            if order.status != "shipped":
                raise BusinessError(detail="订单状态不可确认收货")

            order.status = "completed"
            order.completed_at = datetime.now(UTC)
            await session.flush()

    async def get_merchant_orders(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        status: str | None = None,
        refund_status: str | None = None,
    ) -> tuple[list[OrderOut], int]:
        """获取商家的订单列表"""
        async with get_pg() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise BusinessError(detail="当前用户不是商家")

            orders, total = await orders_repo.get_list_by_merchant(
                session,
                str(merchant.id),
                page,
                page_size,
                status=status,
                refund_status=refund_status,
            )

            # 转换并加载明细
            ordered_out = []
            for o in orders:
                items = await orders_repo.get_items_by_order_id(session, o.id)
                o_out = OrderOut.model_validate(o)
                o_out.items = [
                    OrderItemOut(
                        id=i.id,
                        product_id=i.product_id,
                        quantity=i.quantity,
                        unit_price=i.unit_price,
                        product_name=i.product.name,
                        product_image=i.product.image_url,
                        is_reviewed=False,
                    )
                    for i in items
                ]
                ordered_out.append(o_out)

            return ordered_out, total

    async def auto_receipt_orders(self, days: int = 7) -> int:
        """自动确认超过指定天数的已发货订单"""

        async with get_pg() as session:
            # 计算过期时间点
            expiration_time = datetime.now(UTC) - timedelta(days=days)

            # 查询过期订单
            orders = await orders_repo.get_shipped_orders_before(
                session, expiration_time
            )

            count = 0
            for order in orders:
                order.status = "completed"
                order.completed_at = datetime.now(UTC)
                count += 1

            # 提交事务
            if count > 0:
                await session.commit()

            return count
