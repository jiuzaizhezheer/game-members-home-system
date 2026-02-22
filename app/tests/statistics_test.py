import asyncio

from sqlalchemy import select

from app.database.pgsql import get_pg
from app.entity.pgsql import Merchant
from app.repo import statistics_repo
from app.services.statistics_service import StatisticsService


async def verify_repo():
    async with get_pg() as session:
        merchant = (
            await session.execute(select(Merchant).limit(1))
        ).scalar_one_or_none()
        if not merchant:
            print("No merchant found.")
            return

        print(f"--- Testing Repo for Merchant ID: {merchant.id} ---")

        print("\n[Dashboard Overview]")
        dash = await statistics_repo.get_dashboard_overview(session, merchant.id)
        print(dash)

        print("\n[Sales Trend]")
        trend = await statistics_repo.get_sales_trend(session, merchant.id, 7)
        for t in trend:
            print(t)

        print("\n[Top Products]")
        top = await statistics_repo.get_top_products(session, merchant.id, 3)
        for p in top:
            print(p)


async def verify_service():
    async with get_pg() as session:
        merchant = (
            await session.execute(select(Merchant).limit(1))
        ).scalar_one_or_none()
        if not merchant:
            print("No merchant found.")
            return

        print(f"\n--- Testing Service for User ID: {merchant.user_id} ---")

        svc = StatisticsService()

        print("\n[Dashboard Overview]")
        dash = await svc.get_dashboard_overview(str(merchant.user_id))
        print(dash.model_dump_json(indent=2))

        print("\n[Sales Trend]")
        trend = await svc.get_sales_trend(str(merchant.user_id), 7)
        print(trend.model_dump_json(indent=2))

        print("\n[Top Products]")
        top = await svc.get_top_products(str(merchant.user_id), 3)
        print(top.model_dump_json(indent=2))


async def main():
    print("===============================")
    print("Running Statistics Tests")
    print("===============================\n")
    await verify_repo()
    await verify_service()


if __name__ == "__main__":
    asyncio.run(main())
