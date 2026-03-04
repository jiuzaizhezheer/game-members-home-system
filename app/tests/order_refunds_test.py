import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.database.pgsql import get_pg
from app.entity.pgsql import Merchant, Order, OrderItem, Product, User
from app.main import app
from app.utils.password_util import hash_password
from app.utils.token_util import get_access_token


@pytest.fixture
async def setup_data():
    """Setup mock user, merchant, product, order for the tests"""
    buyer_id = uuid.uuid4()
    merchant_user_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    product_id = uuid.uuid4()
    order_id = uuid.uuid4()

    async with get_pg() as session:
        # 1. Create Buyer User
        buyer = User(
            id=buyer_id,
            username=f"test_buyer_{buyer_id.hex[:8]}",
            email=f"buyer_{buyer_id.hex[:8]}@test.com",
            password_hash=hash_password("password"),
            role="member",
        )
        session.add(buyer)

        # 2. Create Merchant User & Merchant Entity
        merchant_user = User(
            id=merchant_user_id,
            username=f"test_merchant_{merchant_user_id.hex[:8]}",
            email=f"merchant_{merchant_user_id.hex[:8]}@test.com",
            password_hash=hash_password("password"),
            role="merchant",
        )
        session.add(merchant_user)

        merchant = Merchant(
            id=merchant_id,
            user_id=merchant_user_id,
            shop_name=f"Test Shop {merchant_id.hex[:8]}",
            contact_phone="13800138000",
        )
        session.add(merchant)

        # 3. Create Product
        product = Product(
            id=product_id,
            merchant_id=merchant_id,
            name="Test Refund Product",
            price=Decimal("100.00"),
            stock=10,
            status="on",
        )
        session.add(product)

        # 4. Create Order (Paid status to allow refund)
        order = Order(
            id=order_id,
            user_id=buyer_id,
            order_no=f"ORDER_{order_id.hex[:12]}",
            status="paid",
            total_amount=Decimal("100.00"),
            paid_at=datetime.now(UTC),
        )
        session.add(order)

        # 5. Create OrderItem
        order_item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=1,
            unit_price=Decimal("100.00"),
        )
        session.add(order_item)
        # Session will commit on exit

    # Generate tokens
    buyer_token = get_access_token(str(buyer_id), "member")
    merchant_token = get_access_token(str(merchant_user_id), "merchant")

    yield {
        "buyer_id": buyer_id,
        "merchant_user_id": merchant_user_id,
        "order_id": order_id,
        "product_id": product_id,
        "buyer_token": buyer_token,
        "merchant_token": merchant_token,
    }

    # Cleanup
    async with get_pg() as clean_session:
        from sqlalchemy import text

        await clean_session.execute(
            text("DELETE FROM order_refunds WHERE order_id = :oid"),
            {"oid": order_id},
        )
        await clean_session.execute(
            text("DELETE FROM order_items WHERE order_id = :oid"), {"oid": order_id}
        )
        await clean_session.execute(
            text("DELETE FROM orders WHERE id = :oid"), {"oid": order_id}
        )
        await clean_session.execute(
            text("DELETE FROM products WHERE id = :pid"), {"pid": product_id}
        )
        await clean_session.execute(
            text("DELETE FROM merchants WHERE id = :mid"), {"mid": merchant_id}
        )
        await clean_session.execute(
            text("DELETE FROM users WHERE id IN (:bid, :mid)"),
            {"bid": buyer_id, "mid": merchant_user_id},
        )


@pytest.mark.asyncio
async def test_order_refund_workflow(setup_data):
    """Combined test for refund lifecycle, audit rejection, and merchant view (Windows fix)"""
    data = setup_data
    order_id = data["order_id"]
    buyer_token = data["buyer_token"]
    merchant_token = data["merchant_token"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # --- PART 1: Refund Lifecycle (Apply -> Approve) ---
        # 1. User Apply for Refund
        payload = {"reason": "Test Refund Reason"}
        response = await ac.post(
            f"/api/orders/{order_id}/refund",
            json=payload,
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert response.status_code == 201
        refund_id = response.json()["data"]["id"]

        # 2. Merchant view refund detail
        response = await ac.get(
            f"/api/orders/{order_id}/refund",
            headers={"Authorization": f"Bearer {merchant_token}"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["reason"] == "Test Refund Reason"

        # 3. Merchant Audit Approve
        audit_payload = {"status": "approved", "merchant_reply": "Agreed"}
        response = await ac.post(
            f"/api/merchants/orders/refunds/{refund_id}/audit",
            json=audit_payload,
            headers={"Authorization": f"Bearer {merchant_token}"},
        )
        assert response.status_code == 200

        # Verify Approved Statuses
        async with get_pg() as session:
            order = await session.get(Order, order_id)
            assert order.status == "refunded"
            product = await session.get(Product, data["product_id"])
            assert product.stock == 11

        # --- PART 2: Re-apply and Reject (Testing rejection logic) ---
        # Reset order status to paid and DELETE OLD REFUND for testing rejection
        async with get_pg() as session:
            # Delete old refund
            await session.execute(
                text("DELETE FROM order_refunds WHERE order_id = :oid"),
                {"oid": order_id},
            )
            # Reset order and product
            order = await session.get(Order, order_id)
            order.status = "paid"
            product = await session.get(Product, data["product_id"])
            product.stock = 10
            # commit is automatic in get_pg

        # 1. Apply again
        response = await ac.post(
            f"/api/orders/{order_id}/refund",
            json={"reason": "Reject me"},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert response.status_code == 201
        new_refund_id = response.json()["data"]["id"]

        # 2. Reject
        response = await ac.post(
            f"/api/merchants/orders/refunds/{new_refund_id}/audit",
            json={"status": "rejected", "merchant_reply": "No way"},
            headers={"Authorization": f"Bearer {merchant_token}"},
        )
        assert response.status_code == 200

        # Verify Rejected Statuses
        async with get_pg() as session:
            order = await session.get(Order, order_id)
            assert order.status == "paid"
            product = await session.get(Product, data["product_id"])
            assert product.stock == 10
