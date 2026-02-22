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


if __name__ == "__main__":
    asyncio.run(table_structure_patch_10())
