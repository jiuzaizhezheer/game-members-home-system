"""商家服务层：商家店铺业务逻辑"""

from app.common.constants import MERCHANT_NOT_FOUND
from app.common.errors import NotFoundError
from app.database.pgsql import get_pg
from app.repo import merchants_repo
from app.schemas.merchant import (
    MerchantOut,
    MerchantUpdateIn,
)


class MerchantService:
    """商家服务（只管理商家店铺信息）"""

    async def get_by_user_id(self, user_id: str) -> MerchantOut:
        """根据用户ID获取商家信息"""
        async with get_pg() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise NotFoundError(MERCHANT_NOT_FOUND)
            return MerchantOut.model_validate(merchant)

    async def update(self, id: str, payload: MerchantUpdateIn) -> MerchantOut:
        """更新商家信息"""
        async with get_pg() as session:
            merchant = await merchants_repo.get_by_id(session, id)
            if not merchant:
                raise NotFoundError(MERCHANT_NOT_FOUND)

            # 只更新提供的字段
            update_data = payload.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(merchant, key, value)

            await merchants_repo.update(session)
            return MerchantOut.model_validate(merchant)
