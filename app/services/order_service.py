"""订单服务层：订单业务逻辑"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

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
from app.schemas.order import OrderCreateIn, OrderItemOut, OrderOut
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

                # 计算小计
                subtotal = product.price * ci.quantity
                total_amount += subtotal

                # 准备订单明细
                order_items_to_create.append(
                    OrderItem(
                        product_id=ci.product_id,
                        quantity=ci.quantity,
                        unit_price=product.price,
                        product=product,  # 赋值以便下文直接获取名称
                    )
                )

            # 4. 创建订单记录
            new_order = Order(
                user_id=uuid.UUID(user_id),
                address_id=payload.address_id,
                order_no=generate_order_no(),
                status="pending",
                total_amount=total_amount,
            )
            await orders_repo.create(session, new_order)

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
                items=[
                    OrderItemOut(
                        id=oi.id,
                        product_id=oi.product_id,
                        quantity=oi.quantity,
                        unit_price=oi.unit_price,
                        product_name=oi.product.name,
                        product_image=oi.product.image_url,
                    )
                    for oi in order_items_to_create
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

            # 转换并加载明细 (实际应在 Repo 层优化加载)
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
                        product_name=i.product.name,  # 假如 lazy="selectin" 生效
                        product_image=i.product.image_url,
                    )
                    for i in items
                ]
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

            # 3. 更新状态
            order.status = "paid"
            order.paid_at = datetime.now(UTC)
            await session.flush()

    async def ship_order(self, order_id: str) -> None:
        """订单发货 (需鉴权: 商家是否拥有该订单商品)"""
        async with get_pg() as session:
            order = await orders_repo.get_by_id(session, order_id)
            if not order:
                raise NotFoundError("订单不存在")

            if order.status != "paid":
                # raise BusinessError("订单状态不可发货")
                # 暂时允许 pending -> shipped (为了方便测试), 或者严格 paid -> shipped
                if order.status != "paid":
                    raise BusinessError(detail="订单未支付或状态异常")

            order.status = "shipped"
            order.shipped_at = datetime.now(UTC)
            await session.flush()

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
    ) -> tuple[list[OrderOut], int]:
        """获取商家的订单列表"""
        async with get_pg() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise BusinessError(detail="当前用户不是商家")

            orders, total = await orders_repo.get_list_by_merchant(
                session, str(merchant.id), page, page_size, status=status
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
