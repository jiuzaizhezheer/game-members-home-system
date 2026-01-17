import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL)


# 新增 products 表中 image_url 字段
async def table_structure_patch_1():

    async with engine.begin() as conn:
        print("Adding image_url column to products table...")
        await conn.execute(
            text(
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS image_url varchar(512);"
            )
        )
        print("Done!")

    await engine.dispose()


# 修改 merchants 表中 contact_phone 字段长度为 11
async def table_structure_patch_2():

    async with engine.begin() as conn:
        print("Modifying contact_phone length in merchants table...")
        await conn.execute(
            text(
                "ALTER TABLE merchants ALTER COLUMN contact_phone TYPE varchar(11) USING contact_phone::varchar(11);"
            )
        )
        print("Done!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(table_structure_patch_2())
