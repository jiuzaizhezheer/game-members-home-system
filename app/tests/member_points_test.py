import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

# Import repos as modules explicitly to avoid namespace issues in tests
from app.database.pgsql import get_pg
from app.entity.pgsql import Merchant, Order, OrderItem, Product, User
from app.main import app
from app.utils.password_util import hash_password


@pytest.fixture
async def cleanup():
    """Cleanup test users and data after tests"""
    test_usernames = []
    yield test_usernames

    async with get_pg() as session:
        for username in test_usernames:
            # 1. 获取用户ID
            if username:
                user_id_res = await session.execute(
                    text("SELECT id FROM users WHERE username = :u"), {"u": username}
                )
                user_id = user_id_res.scalar()
                if user_id:
                    await session.execute(
                        text("DELETE FROM point_logs WHERE user_id = :u"),
                        {"u": user_id},
                    )
                    await session.execute(
                        text(
                            "DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE user_id = :u)"
                        ),
                        {"u": user_id},
                    )
                    await session.execute(
                        text("DELETE FROM orders WHERE user_id = :u"), {"u": user_id}
                    )
                    # Clean up merchants and merchant users created during tests
                    await session.execute(
                        text(
                            "DELETE FROM merchants WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'm_%')"
                        )
                    )
                    await session.execute(
                        text("DELETE FROM users WHERE username LIKE 'm_%'")
                    )
                    await session.execute(
                        text("DELETE FROM users WHERE id = :u"), {"u": user_id}
                    )
                    await session.commit()


@pytest.mark.asyncio
async def test_member_points_full_workflow(cleanup):
    """测试完整会员积分生命周期：注册奖励 -> 消费奖励 -> 成长等级 -> 评价奖励"""
    suffix = uuid.uuid4().hex[:6]
    username = f"point_user_{suffix}"
    email = f"point_{suffix}@test.com"
    password = "password123"
    cleanup.append(username)

    # Ensure MongoDB/Beanie is initialized
    from app.database.mongodb import init_mongodb

    await init_mongodb()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # --- 0. 获取验证码并从 Redis 绕过 ---
        from app.database.redis import get_redis

        captcha_resp = await ac.get("/api/auths/captcha")
        assert captcha_resp.status_code == 200
        captcha_id = captcha_resp.json()["data"]["id"]

        async with get_redis() as redis:
            captcha_code = await redis.get(f"captcha:{captcha_id}")
            assert captcha_code is not None

        # --- 1. 用户注册 ---
        register_payload = {
            "username": username,
            "email": email,
            "password": password,
            "role": "member",
            "captcha_id": captcha_id,
            "captcha_code": captcha_code,
        }
        response = await ac.post("/api/auths/register", json=register_payload)
        assert response.status_code == 201  # 注册返回 201

        # --- 2. 登录并验证初始积分 ---
        login_payload = {"email": email, "password": password, "role": "member"}
        response = await ac.post("/api/auths/login", json=login_payload)
        assert response.status_code == 200
        token = response.json()["data"]["access_token"]

        response = await ac.get(
            "/api/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        profile = response.json()["data"]
        assert Decimal(str(profile["points"])) == Decimal("100.0")  # 注册赠送 100
        assert profile["level"] == "bronze"
        buyer_id = profile["id"]

        # --- 3. 构造一笔大额订单并支付 (模拟成长等级晋升) ---
        # 首先需要创建一个商家和商品
        async with get_pg() as session:
            # 创建 mock 商家
            m_id = uuid.uuid4()
            m_user_id = uuid.uuid4()
            m_user = User(
                id=m_user_id,
                username=f"m_{suffix}",
                email=f"m_{suffix}@test.com",
                password_hash=hash_password("p"),
                role="merchant",
            )
            session.add(m_user)
            merchant = Merchant(
                id=m_id,
                user_id=m_user_id,
                shop_name=f"Point Test Shop {suffix}",
                contact_phone=None,
                shop_desc=None,
                logo_url=None,
            )
            session.add(merchant)
            # 这里的金额要能升到银级 (>= 2000) -> 改为 99.00 测试精度
            product_id = uuid.uuid4()
            product = Product(
                id=product_id,
                merchant_id=m_id,
                name="Precise Item",
                price=Decimal("99.00"),
                stock=100,
                status="on",
            )
            session.add(product)

            # 创建订单
            order_id = uuid.uuid4()
            order = Order(
                id=order_id,
                user_id=uuid.UUID(buyer_id),
                order_no=f"P_ORDER_{suffix}",
                status="pending",
                total_amount=Decimal("99.00"),
            )
            session.add(order)

            # 创建订单项 (必须，否则评价路由会报错)
            order_item = OrderItem(
                id=uuid.uuid4(),
                order_id=order_id,
                product_id=product_id,
                quantity=1,
                unit_price=Decimal("99.00"),
            )
            session.add(order_item)
            await session.commit()

        # 调用支付接口 (假设内部逻辑会触发 PointService)
        # 考虑到简化，如果支付路由涉及外部系统可能麻烦，但我这里调用的是系统内部 flow
        response = await ac.post(
            f"/api/orders/{order_id}/pay", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        # --- 4. 验证支付后的积分与等级 ---
        response = await ac.get(
            "/api/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        profile = response.json()["data"]
        # 初始 100 + 奖励 (99.00 / 10 = 9.9) = 109.9
        assert Decimal(str(profile["points"])) == Decimal("109.9")
        # 累计消费 99 < 2000，应保持 bronze
        assert profile["level"] == "bronze"

        # --- 5. 提交评价奖励 ---
        # 首先完成订单 (模拟完成)
        async with get_pg() as session:
            stmt = text("UPDATE orders SET status = 'completed' WHERE id = :oid")
            await session.execute(stmt, {"oid": order_id})
            await session.commit()  # Commit the order status update

        review_payload = {
            "order_id": str(order_id),
            "product_id": str(product_id),
            "rating": 5,
            "content": "Excellent service!",
            "images": [],
        }
        response = await ac.post(
            "/api/reviews",
            json=review_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

        # 验证评价后积分：109.9 + 20 = 129.9
        response = await ac.get(
            "/api/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert Decimal(str(response.json()["data"]["points"])) == Decimal("129.9")

        # --- 6. 查看积分变动流水 ---
        response = await ac.get(
            "/api/users/me/points", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        history = response.json()["data"]
        assert history["total"] >= 3  # 注册、支付、评价
        reasons = [item["reason"] for item in history["items"]]
        assert "用户注册赠送" in reasons
        assert "订单支付奖励" in reasons
        assert "发表评价奖励" in reasons

    # 清理商家和商品 (cleanup fixture 没管这些手动加的)
    async with get_pg() as session:
        await session.execute(
            text("DELETE FROM products WHERE id = :pid"), {"pid": product_id}
        )
        await session.execute(
            text("DELETE FROM merchants WHERE id = :mid"), {"mid": m_id}
        )
        await session.execute(
            text("DELETE FROM users WHERE id = :uid"), {"uid": m_user_id}
        )
