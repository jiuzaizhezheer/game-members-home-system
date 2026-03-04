from app.common.errors import NotFoundError
from app.database.pgsql import get_pg
from app.entity.pgsql import Banner
from app.repo import banners_repo
from app.schemas.banner import BannerIn, BannerListOut, BannerOut, BannerUpdateIn


class BannerService:
    async def get_public_banners(self) -> list[BannerOut]:
        """获取首页展示的 Banner (仅启用的)"""
        async with get_pg() as session:
            banners = await banners_repo.get_all(session, only_active=True)
            return [BannerOut.model_validate(b) for b in banners]

    async def get_admin_banners(
        self, page: int = 1, page_size: int = 20
    ) -> BannerListOut:
        """获取管理员管理的 Banner 列表 (全部)"""
        async with get_pg() as session:
            banners, total = await banners_repo.get_list_paged(session, page, page_size)
            return BannerListOut(
                items=[BannerOut.model_validate(b) for b in banners], total=total
            )

    async def create_banner(self, payload: BannerIn) -> BannerOut:
        """创建 Banner"""
        async with get_pg() as session:
            banner = Banner(**payload.model_dump())
            await banners_repo.create(session, banner)
            await session.commit()
            return BannerOut.model_validate(banner)

    async def update_banner(self, banner_id: str, payload: BannerUpdateIn) -> BannerOut:
        """更新 Banner (支持部分更新)"""
        async with get_pg() as session:
            banner = await banners_repo.get_by_id(session, banner_id)
            if not banner:
                raise NotFoundError("Banner 不存在")

            # 更新字段
            data = payload.model_dump(exclude_unset=True)
            for key, value in data.items():
                setattr(banner, key, value)

            await session.commit()
            return BannerOut.model_validate(banner)

    async def delete_banner(self, banner_id: str) -> None:
        """删除 Banner"""
        async with get_pg() as session:
            banner = await banners_repo.get_by_id(session, banner_id)
            if not banner:
                raise NotFoundError("Banner 不存在")

            await banners_repo.delete(session, banner)
            await session.commit()


banner_service = BannerService()
