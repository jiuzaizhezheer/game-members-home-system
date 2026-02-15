"""购物车服务层：购物车业务逻辑"""

import uuid
from decimal import Decimal

from sqlalchemy import select

from app.common.constants import (
    PRODUCT_NOT_FOUND,
    PRODUCT_OFF_SHELF,
    PRODUCT_STOCK_NOT_ENOUGH,
)
from app.common.errors import BusinessError, NotFoundError
from app.database.pgsql import get_pg
from app.entity.pgsql import Cart, CartItem
from app.repo import carts_repo, products_repo
from app.schemas.cart import CartItemAddIn, CartItemOut, CartItemUpdateIn, CartOut


class CartService:
    """购物车服务"""

    async def get_my_cart(self, user_id: str, cart_id: str | None = None) -> CartOut:
        """获取我的指定购物车或最新活动购物车"""
        async with get_pg() as session:
            # 1. 获取购物车
            if cart_id:
                cart = await carts_repo.get_by_id(session, uuid.UUID(cart_id))
                if not cart or str(cart.user_id) != user_id:
                    raise NotFoundError("购物车不存在")
            else:
                cart = await carts_repo.get_active_by_user_id(session, user_id)
                # 如果完全没有活动购物车，创建一个默认的
                if not cart:
                    cart = Cart(user_id=uuid.UUID(user_id), name="默认购物车")
                    cart = await carts_repo.create(session, cart)

            # 2. 获取明细
            items = await carts_repo.get_items(session, cart.id)

            # 3. 组装数据
            cart_items_out = []
            total_amount = Decimal("0.00")
            total_quantity = 0

            for item in items:
                product = await products_repo.get_by_id(session, str(item.product_id))
                if not product:
                    await carts_repo.delete_item(session, item)
                    continue

                current_price = Decimal(str(product.price))
                subtotal = current_price * item.quantity

                cart_items_out.append(
                    CartItemOut(
                        id=item.id,
                        product_id=product.id,
                        product_name=product.name,
                        product_image=product.image_url,
                        unit_price=current_price,
                        quantity=item.quantity,
                        subtotal=subtotal,
                    )
                )
                total_amount += subtotal
                total_quantity += item.quantity

            return CartOut(
                id=cart.id,
                name=cart.name,
                is_checked_out=cart.is_checked_out,
                items=cart_items_out,
                total_amount=total_amount,
                total_quantity=total_quantity,
            )

    async def get_all_carts(self, user_id: str) -> list[CartOut]:
        """获取用户所有购物车列表（简化版，不含明细以提高性能）"""
        async with get_pg() as session:
            carts = await carts_repo.get_all_by_user_id(session, user_id)
            # 这里简单处理，只返回基本信息。如果前端需要明细，可另行请求 get_my_cart(id)
            return [
                CartOut(
                    id=c.id,
                    name=c.name,
                    is_checked_out=c.is_checked_out,
                    items=[],
                    total_amount=Decimal("0.00"),
                    total_quantity=0,
                )
                for c in carts
            ]

    async def create_cart(self, user_id: str, name: str) -> CartOut:
        """创建一个全新的购物车"""
        async with get_pg() as session:
            new_cart = Cart(user_id=uuid.UUID(user_id), name=name)
            await carts_repo.create(session, new_cart)
            return CartOut(
                id=new_cart.id,
                name=new_cart.name,
                is_checked_out=False,
                items=[],
                total_amount=Decimal("0.00"),
                total_quantity=0,
            )

    async def add_item(self, user_id: str, payload: CartItemAddIn) -> None:
        """添加商品到当前活动购物车"""
        async with get_pg() as session:
            product = await products_repo.get_by_id(session, str(payload.product_id))
            if not product:
                raise NotFoundError(PRODUCT_NOT_FOUND)
            if product.status != "on":
                raise BusinessError(detail=PRODUCT_OFF_SHELF)

            if product.stock < payload.quantity:
                raise BusinessError(detail=PRODUCT_STOCK_NOT_ENOUGH)

            # 获取主活动购物车
            cart = await carts_repo.get_active_by_user_id(session, user_id)
            if not cart:
                cart = Cart(user_id=uuid.UUID(user_id), name="默认购物车")
                cart = await carts_repo.create(session, cart)

            cart_item = await carts_repo.get_item_by_product(
                session, cart.id, payload.product_id
            )

            if cart_item:
                new_quantity = cart_item.quantity + payload.quantity
                if new_quantity > product.stock:
                    raise BusinessError(detail=PRODUCT_STOCK_NOT_ENOUGH)
                cart_item.quantity = new_quantity
                cart_item.unit_price = product.price
                await carts_repo.update_item(session, cart_item)
            else:
                new_item = CartItem(
                    cart_id=cart.id,
                    product_id=product.id,
                    quantity=payload.quantity,
                    unit_price=product.price,
                )
                await carts_repo.add_item(session, new_item)

    async def update_item(
        self, user_id: str, item_id: str, payload: CartItemUpdateIn
    ) -> None:
        """更新当前活动购物车中的商品数量"""
        async with get_pg() as session:
            cart = await carts_repo.get_active_by_user_id(session, user_id)
            if not cart:
                raise NotFoundError("活动购物车不存在")

            # 查询 Item
            stmt = select(CartItem).where(CartItem.id == item_id)
            item = (await session.execute(stmt)).scalar_one_or_none()

            if not item or item.cart_id != cart.id:
                raise NotFoundError("购物车商品不存在")

            product = await products_repo.get_by_id(session, str(item.product_id))
            if not product:
                await carts_repo.delete_item(session, item)
                raise NotFoundError(PRODUCT_NOT_FOUND)

            if payload.quantity > product.stock:
                raise BusinessError(detail=PRODUCT_STOCK_NOT_ENOUGH)

            item.quantity = payload.quantity
            item.unit_price = product.price
            await carts_repo.update_item(session, item)

    async def remove_item(self, user_id: str, item_id: str) -> None:
        """移除商品"""
        async with get_pg() as session:
            # 简化逻辑：只要是该用户拥有的任意购物车里的项目都可以删，或者限定当前活动购物车
            # 这里我们限定当前活动购物车以保持逻辑严密
            cart = await carts_repo.get_active_by_user_id(session, user_id)
            if not cart:
                return

            stmt = select(CartItem).where(CartItem.id == item_id)
            item = (await session.execute(stmt)).scalar_one_or_none()

            if item and item.cart_id == cart.id:
                await carts_repo.delete_item(session, item)

    async def clear_cart(self, user_id: str) -> None:
        """清空当前活动购物车"""
        async with get_pg() as session:
            cart = await carts_repo.get_active_by_user_id(session, user_id)
            if cart:
                await carts_repo.clear_items(session, cart.id)
