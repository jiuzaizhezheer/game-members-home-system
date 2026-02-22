import asyncio
import os
import sys

# 将项目根目录添加到 python 路径
sys.path.append(os.getcwd())

from sqlalchemy import func, select

from app.database.pgsql import get_pg
from app.entity.pgsql import Favorite, Product


async def init_popularity():
    print("Starting popularity score initialization (Weighted Formula)...")
    async with get_pg() as session:
        # 1. 首先同步收藏量 (从 favorites 表中统计)
        print("Synchronizing favorites_count for all products...")
        # 统计每个商品的收藏数
        fav_counts_stmt = select(
            Favorite.product_id, func.count(Favorite.user_id).label("count")
        ).group_by(Favorite.product_id)

        fav_results = await session.execute(fav_counts_stmt)
        fav_mapping = {row.product_id: row.count for row in fav_results.all()}

        # 2. 获取所有商品并计算分值
        stmt = select(Product)
        result = await session.execute(stmt)
        products = result.scalars().all()

        count = 0
        for product in products:
            # 更新冗余字段
            product.favorites_count = fav_mapping.get(product.id, 0)
            # 点赞量暂时默认为目前数据 (如果未来有 likes 表也可以类似统计)

            # 人气分计算公式：销量*10 + 收藏*5 + 点赞*2 + 浏览*1
            product.popularity_score = (
                (product.sales_count * 10)
                + (product.favorites_count * 5)
                + (product.likes_count * 2)
                + (product.views_count * 1)
            )
            count += 1

        await session.flush()
        print(f"Successfully updated popularity scores for {count} products.")
        print("Formula used: (Sales*10) + (Favs*5) + (Likes*2) + (Views*1)")


if __name__ == "__main__":
    asyncio.run(init_popularity())
