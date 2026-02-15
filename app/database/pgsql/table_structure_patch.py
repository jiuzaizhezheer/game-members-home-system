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


if __name__ == "__main__":
    asyncio.run(table_structure_patch_6())
