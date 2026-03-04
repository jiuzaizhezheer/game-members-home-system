import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import DATABASE_URL

pg_engine = create_async_engine(DATABASE_URL)


# 新增 products 表中 image_url 字段
async def table_structure_patch_1():

    async with pg_engine.begin() as conn:
        print("Adding image_url column to products table...")
        await conn.execute(
            text(
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS image_url varchar(512);"
            )
        )
        print("Done!")

    await pg_engine.dispose()


# 修改 merchants 表中 contact_phone 字段长度为 11
async def table_structure_patch_2():

    async with pg_engine.begin() as conn:
        print("Modifying contact_phone length in merchants table...")
        await conn.execute(
            text(
                "ALTER TABLE merchants ALTER COLUMN contact_phone TYPE varchar(11) USING contact_phone::varchar(11);"
            )
        )
        print("Done!")

    await pg_engine.dispose()


# 删除 messages 和 comments 表（迁移至 MongoDB）
async def table_structure_patch_3():

    async with pg_engine.begin() as conn:
        print("Dropping messages and comments tables...")
        await conn.execute(text("DROP TABLE IF EXISTS messages CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS comments CASCADE;"))
        print("Done!")

    await pg_engine.dispose()


# 购物车支持多购物车（移除唯一约束，新增名称和结算状态）
async def table_structure_patch_4():

    async with pg_engine.begin() as conn:
        print("Refactoring carts table for multi-cart support...")
        # 1. 移除 user_id 的唯一约束 (PostgreSQL 默认命名通常为 carts_user_id_key)
        await conn.execute(
            text("ALTER TABLE carts DROP CONSTRAINT IF EXISTS carts_user_id_key;")
        )

        # 2. 新增 name 和 is_checked_out 字段
        await conn.execute(
            text(
                "ALTER TABLE carts ADD COLUMN IF NOT EXISTS name varchar(128) NOT NULL DEFAULT '默认购物车';"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE carts ADD COLUMN IF NOT EXISTS is_checked_out boolean NOT NULL DEFAULT false;"
            )
        )


# 商家表新增 logo_url 字段
async def table_structure_patch_5():

    async with pg_engine.begin() as conn:
        print("Adding logo_url column to merchants table...")
        await conn.execute(
            text(
                "ALTER TABLE merchants ADD COLUMN IF NOT EXISTS logo_url varchar(512);"
            )
        )
        print("Done!")


# 用户表新增 avatar_url 字段
async def table_structure_patch_6():

    async with pg_engine.begin() as conn:
        print("Adding avatar_url column to users table...")
        await conn.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url varchar(512);")
        )
        print("Done!")

    await pg_engine.dispose()


# 社区功能表结构补丁 (Groups, Posts)
# Comments 和 Likes 使用 MongoDB
async def table_structure_patch_7():
    async with pg_engine.begin() as conn:
        print("Creating community tables (community_groups, posts)...")

        # 1. community_groups
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS community_groups (
                id UUID PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                cover_image TEXT,
                member_count INTEGER DEFAULT 0 NOT NULL,
                post_count INTEGER DEFAULT 0 NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """
            )
        )

        # 1.1 增量更新 community_groups
        await conn.execute(
            text(
                """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='community_groups' AND column_name='member_count') THEN
                    ALTER TABLE community_groups ADD COLUMN member_count INTEGER DEFAULT 0 NOT NULL;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='community_groups' AND column_name='post_count') THEN
                    ALTER TABLE community_groups ADD COLUMN post_count INTEGER DEFAULT 0 NOT NULL;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='community_groups' AND column_name='cover_image') THEN
                    ALTER TABLE community_groups ADD COLUMN cover_image TEXT;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='community_groups' AND column_name='is_active') THEN
                    ALTER TABLE community_groups ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL;
                END IF;
            END $$;
        """
            )
        )

        # 2. posts (注意：likes_count 是复数)
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS posts (
                id UUID PRIMARY KEY,
                group_id UUID NOT NULL,
                user_id UUID NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                images TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
                videos TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
                view_count INTEGER DEFAULT 0 NOT NULL,
                likes_count INTEGER DEFAULT 0 NOT NULL,
                comment_count INTEGER DEFAULT 0 NOT NULL,
                is_top BOOLEAN DEFAULT FALSE NOT NULL,
                is_hidden BOOLEAN DEFAULT FALSE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """
            )
        )

        # 2.1 增量更新 posts
        await conn.execute(
            text(
                """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='images') THEN
                    ALTER TABLE posts ADD COLUMN images TEXT[] DEFAULT '{}'::TEXT[] NOT NULL;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='videos') THEN
                    ALTER TABLE posts ADD COLUMN videos TEXT[] DEFAULT '{}'::TEXT[] NOT NULL;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='view_count') THEN
                    ALTER TABLE posts ADD COLUMN view_count INTEGER DEFAULT 0 NOT NULL;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='likes_count') THEN
                    ALTER TABLE posts ADD COLUMN likes_count INTEGER DEFAULT 0 NOT NULL;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='comment_count') THEN
                    ALTER TABLE posts ADD COLUMN comment_count INTEGER DEFAULT 0 NOT NULL;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='is_top') THEN
                    ALTER TABLE posts ADD COLUMN is_top BOOLEAN DEFAULT FALSE NOT NULL;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='is_hidden') THEN
                    ALTER TABLE posts ADD COLUMN is_hidden BOOLEAN DEFAULT FALSE NOT NULL;
                END IF;
            END $$;
        """
            )
        )

        # 3. 索引
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_posts_group ON posts (group_id, created_at);"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_posts_user ON posts (user_id, created_at);"
            )
        )

        print("Community tables created/verified!")

    await pg_engine.dispose()


# 社区分组支持商家 (新增 merchant_id)
async def table_structure_patch_8():
    async with pg_engine.begin() as conn:
        print("Adding merchant_id to community_groups...")
        await conn.execute(
            text(
                """
            ALTER TABLE community_groups
            ADD COLUMN IF NOT EXISTS merchant_id UUID;
        """
            )
        )
        await conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_community_groups_merchant ON community_groups(merchant_id);
        """
            )
        )
        print("Done!")

    await pg_engine.dispose()


# 商品表支持人气分多维度权重 (新增 favorites_count, likes_count)
async def table_structure_patch_9():
    async with pg_engine.begin() as conn:
        print("Adding favorites_count and likes_count to products...")
        await conn.execute(
            text(
                """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS favorites_count INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS likes_count INTEGER NOT NULL DEFAULT 0;
        """
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_products_favorites ON products (favorites_count DESC);"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_products_likes ON products (likes_count DESC);"
            )
        )
        print("Done!")

    await pg_engine.dispose()


# 订单表增加物流信息 (新增 courier_name, tracking_no)
async def table_structure_patch_10():
    async with pg_engine.begin() as conn:
        print("Adding logistics info columns to orders...")
        await conn.execute(
            text(
                """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS courier_name VARCHAR(64),
            ADD COLUMN IF NOT EXISTS tracking_no VARCHAR(64);
        """
            )
        )
        print("Done!")

    await pg_engine.dispose()


# 管理员操作日志表
async def table_structure_patch_11():
    async with pg_engine.begin() as conn:
        print("Creating admin_logs table...")
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS admin_logs (
                id          uuid PRIMARY KEY,
                admin_id    uuid NOT NULL,
                action      varchar(64) NOT NULL,
                target_type varchar(32) NOT NULL,
                target_id   varchar(64) NOT NULL,
                detail      jsonb,
                created_at  timestamptz NOT NULL DEFAULT now()
            );
        """
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id ON admin_logs(admin_id);"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_admin_logs_created_at ON admin_logs(created_at DESC);"
            )
        )
        print("Done!")

    await pg_engine.dispose()


# 售后退款表及订单状态扩展
async def table_structure_patch_12():
    async with pg_engine.begin() as conn:
        print("Creating order_refunds table and updating orders status constraint...")

        # 1. 创建 order_refunds
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS order_refunds (
                id              uuid PRIMARY KEY,
                order_id        uuid NOT NULL,
                user_id         uuid NOT NULL,
                reason          varchar(255) NOT NULL,
                amount          numeric(12,2) NOT NULL CHECK (amount >= 0),
                status          varchar(16) NOT NULL DEFAULT 'pending',
                merchant_reply  varchar(255),
                created_at      timestamptz NOT NULL DEFAULT now(),
                updated_at      timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT chk_order_refunds_status CHECK (status IN ('pending', 'approved', 'rejected'))
            );
            """
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_order_refunds_order ON order_refunds(order_id);"
            )
        )

        # 2. 扩展 orders 表 status 约束
        # PostgreSQL 不支持直接修改 CHECK 约束，通常需要先删再加
        # asyncpg 不支持在一个 execute 中执行多个命令，需要分开
        await conn.execute(
            text("ALTER TABLE orders DROP CONSTRAINT IF EXISTS chk_orders_status;")
        )
        await conn.execute(
            text(
                """
            ALTER TABLE orders ADD CONSTRAINT chk_orders_status
            CHECK (status IN ('pending','paid','shipped','completed','cancelled','refunding','refunded','closed'));
            """
            )
        )
        print("Done!")

    await pg_engine.dispose()


# 订单表增加退款状态标记 (新增 refund_status)，并修复状态约束
async def table_structure_patch_13():
    async with pg_engine.begin() as conn:
        print("Adding refund_status to orders and fixing constraints...")

        # 1. 增加 refund_status 字段
        await conn.execute(
            text(
                "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_status VARCHAR(16);"
            )
        )

        # 2. 增加 refund_status 约束
        await conn.execute(
            text(
                "ALTER TABLE orders DROP CONSTRAINT IF EXISTS chk_orders_refund_status;"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE orders ADD CONSTRAINT chk_orders_refund_status CHECK (refund_status IS NULL OR refund_status IN ('pending', 'approved', 'rejected'));"
            )
        )

        # 3. 修复 status 约束 (移除临时的 rejected)
        await conn.execute(
            text("ALTER TABLE orders DROP CONSTRAINT IF EXISTS chk_orders_status;")
        )
        await conn.execute(
            text(
                """
            ALTER TABLE orders ADD CONSTRAINT chk_orders_status
            CHECK (status IN ('pending','paid','shipped','completed','cancelled','refunding','refunded','closed'));
            """
            )
        )
        print("Done!")

    await pg_engine.dispose()


async def table_structure_patch_14():
    """给 products 表添加 rating 和 review_count 字段，用于商品评价系统"""
    async with pg_engine.begin() as conn:
        print("Adding rating and review_count to products...")
        try:
            await conn.execute(
                text(
                    "ALTER TABLE products ADD COLUMN IF NOT EXISTS rating NUMERIC(3,2) NOT NULL DEFAULT 5.00;"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE products ADD COLUMN IF NOT EXISTS review_count INTEGER NOT NULL DEFAULT 0;"
                )
            )
            print("Done!")
        except Exception as e:
            print(f"Failed to apply patch 14: {e}")
            raise

    await pg_engine.dispose()


async def table_structure_patch_15():
    """创建首页轮播图管理表 (banners)"""
    async with pg_engine.begin() as conn:
        print("Creating banners table...")
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS banners (
                id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                title       varchar(128) NOT NULL,
                image_url   varchar(512) NOT NULL,
                link_url    varchar(512),
                sort_order  integer NOT NULL DEFAULT 0,
                is_active   boolean NOT NULL DEFAULT true,
                created_at  timestamptz NOT NULL DEFAULT now(),
                updated_at  timestamptz NOT NULL DEFAULT now()
            );
        """
            )
        )
        await conn.execute(text("COMMENT ON TABLE banners IS '首页轮播图管理表';"))
        print("Done!")

    await pg_engine.dispose()


async def table_structure_patch_16():
    """创建订单物流追踪记录表 (order_logistics)"""
    async with pg_engine.begin() as conn:
        print("Creating order_logistics table...")
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS order_logistics (
                id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                order_id        uuid NOT NULL,
                status_message  varchar(256) NOT NULL,
                location        varchar(128),
                log_time        timestamptz NOT NULL DEFAULT now(),
                created_at      timestamptz NOT NULL DEFAULT now(),
                updated_at      timestamptz NOT NULL DEFAULT now()
            );
        """
            )
        )
        await conn.execute(
            text("COMMENT ON TABLE order_logistics IS '订单物流追踪记录表';")
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_order_logistics_order ON order_logistics(order_id);"
            )
        )
        print("Done!")

    await pg_engine.dispose()


async def table_structure_patch_17():
    """会员积分与成长体系：更新 users 表并创建 point_logs 表"""
    async with pg_engine.begin() as conn:
        print("Updating users table for points and growth...")
        await conn.execute(
            text(
                """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS points INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS total_spent NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
            ADD COLUMN IF NOT EXISTS level VARCHAR(16) NOT NULL DEFAULT 'bronze';
            """
            )
        )

        print("Creating point_logs table...")
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS point_logs (
                id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id         uuid NOT NULL,
                change_amount   integer NOT NULL,
                balance_after   integer NOT NULL,
                reason          varchar(255) NOT NULL,
                related_id      varchar(64),
                created_at      timestamptz NOT NULL DEFAULT now(),
                updated_at      timestamptz NOT NULL DEFAULT now()
            );
            """
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE point_logs ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();"
            )
        )
        await conn.execute(text("COMMENT ON TABLE point_logs IS '用户积分变动日志表';"))
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_point_logs_user ON point_logs(user_id);"
            )
        )
        print("Done!")

    await pg_engine.dispose()


async def table_structure_patch_18():
    """会员积分精度优化：将积分相关字段由 INTEGER 修改为 NUMERIC(12, 2)"""
    async with pg_engine.begin() as conn:
        print("Upgrading points columns to NUMERIC(12, 2) for precision...")

        # 1. 修改 users 表的 points
        await conn.execute(
            text(
                "ALTER TABLE users ALTER COLUMN points TYPE NUMERIC(12, 2) USING points::NUMERIC(12, 2);"
            )
        )

        # 2. 修改 point_logs 表的 change_amount 和 balance_after
        await conn.execute(
            text(
                "ALTER TABLE point_logs ALTER COLUMN change_amount TYPE NUMERIC(12, 2) USING change_amount::NUMERIC(12, 2);"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE point_logs ALTER COLUMN balance_after TYPE NUMERIC(12, 2) USING balance_after::NUMERIC(12, 2);"
            )
        )

        print("Done!")

    await pg_engine.dispose()


async def table_structure_patch_19():
    """优惠券系统：创建 coupons 和 user_coupons 表"""
    async with pg_engine.begin() as conn:
        print("Creating coupons table...")
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS coupons (
                id              uuid PRIMARY KEY,
                merchant_id     uuid,
                title           varchar(128) NOT NULL,
                description     varchar(256),
                discount_type   varchar(16) NOT NULL,
                discount_value  numeric(12, 2) NOT NULL,
                min_spend       numeric(12, 2) NOT NULL DEFAULT 0.00,
                total_quantity  integer NOT NULL DEFAULT 0,
                issued_count    integer NOT NULL DEFAULT 0,
                start_at        timestamptz NOT NULL,
                end_at          timestamptz NOT NULL,
                status          varchar(16) NOT NULL DEFAULT 'active',
                created_at      timestamptz NOT NULL DEFAULT now(),
                updated_at      timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT chk_coupons_discount_value CHECK (discount_value >= 0),
                CONSTRAINT chk_coupons_min_spend CHECK (min_spend >= 0),
                CONSTRAINT chk_coupons_total_quantity CHECK (total_quantity >= 0),
                CONSTRAINT chk_coupons_issued_count CHECK (issued_count >= 0)
            );
            """
            )
        )
        await conn.execute(text("COMMENT ON TABLE coupons IS '优惠券配置表';"))
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_coupons_merchant ON coupons(merchant_id);"
            )
        )

        print("Creating user_coupons table...")
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS user_coupons (
                id              uuid PRIMARY KEY,
                user_id         uuid NOT NULL,
                coupon_id       uuid NOT NULL,
                order_id        uuid,
                status          varchar(16) NOT NULL DEFAULT 'unused',
                used_at         timestamptz,
                created_at      timestamptz NOT NULL DEFAULT now(),
                updated_at      timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT chk_user_coupons_status CHECK (status IN ('unused', 'used', 'expired'))
            );
            """
            )
        )
        await conn.execute(
            text("COMMENT ON TABLE user_coupons IS '用户领取的优惠券清单';")
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_user_coupons_user_status ON user_coupons(user_id, status);"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_user_coupons_coupon ON user_coupons(coupon_id);"
            )
        )

        print("Done!")

    await pg_engine.dispose()


async def table_structure_patch_20():
    """订单表增加优惠券关联及扣减金额字段"""
    async with pg_engine.begin() as conn:
        print("Adding coupon columns to orders table...")
        await conn.execute(
            text(
                """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS user_coupon_id UUID,
            ADD COLUMN IF NOT EXISTS coupon_amount NUMERIC(12, 2);
            """
            )
        )
        await conn.execute(
            text("COMMENT ON COLUMN orders.user_coupon_id IS '使用的优惠券记录ID';")
        )
        await conn.execute(
            text("COMMENT ON COLUMN orders.coupon_amount IS '优惠券抵扣金额';")
        )
        print("Done!")

    await pg_engine.dispose()


async def table_structure_patch_21():
    """订单表增加积分抵扣金额及消耗积分数量字段"""
    async with pg_engine.begin() as conn:
        print("Adding point deduction columns to orders table...")
        await conn.execute(
            text(
                """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS point_deduction_amount NUMERIC(12, 2),
            ADD COLUMN IF NOT EXISTS points_consumed NUMERIC(12, 2);
            """
            )
        )
        await conn.execute(
            text("COMMENT ON COLUMN orders.point_deduction_amount IS '积分抵扣金额';")
        )
        await conn.execute(
            text("COMMENT ON COLUMN orders.points_consumed IS '消耗积分数量';")
        )
        print("Done!")

    await pg_engine.dispose()


if __name__ == "__main__":
    asyncio.run(table_structure_patch_21())
