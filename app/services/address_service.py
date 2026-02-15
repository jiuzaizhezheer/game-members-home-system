"""地址服务层：地址业务逻辑"""

import uuid

from app.common.errors import NotFoundError
from app.database.pgsql import get_pg
from app.entity.pgsql import Address
from app.repo import addresses_repo
from app.schemas.address import AddressCreateIn, AddressOut, AddressUpdateIn


class AddressService:
    """地址服务"""

    async def get_my_addresses(self, user_id: str) -> list[AddressOut]:
        """获取我的地址列表"""
        async with get_pg() as session:
            items = await addresses_repo.get_list_by_user_id(session, user_id)
            return [AddressOut.model_validate(item) for item in items]

    async def add_address(self, user_id: str, payload: AddressCreateIn) -> AddressOut:
        """新增地址"""
        async with get_pg() as session:
            # 如果设置为默认，先取消原有的默认
            if payload.is_default:
                await addresses_repo.unset_default_for_user(session, user_id)

            # 如果这是第一条地址，自动设为默认 (可选)
            # existing = await addresses_repo.get_list_by_user_id(session, user_id)
            # is_default = payload.is_default or not existing

            new_address = Address(
                user_id=uuid.UUID(user_id),
                receiver_name=payload.receiver_name,
                phone=payload.phone,
                province=payload.province,
                city=payload.city,
                district=payload.district,
                detail=payload.detail,
                is_default=payload.is_default,
            )
            await addresses_repo.create(session, new_address)
            return AddressOut.model_validate(new_address)

    async def update_address(
        self, user_id: str, address_id: str, payload: AddressUpdateIn
    ) -> AddressOut:
        """修改地址"""
        async with get_pg() as session:
            address = await addresses_repo.get_by_id(session, address_id)
            if not address or str(address.user_id) != user_id:
                raise NotFoundError("地址未找到")

            # 如果要把该地址设为默认
            if payload.is_default is True and not address.is_default:
                await addresses_repo.unset_default_for_user(session, user_id)

            # 更新字段
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(address, field, value)

            await addresses_repo.update_address(session, address)
            return AddressOut.model_validate(address)

    async def delete_address(self, user_id: str, address_id: str) -> None:
        """删除地址"""
        async with get_pg() as session:
            address = await addresses_repo.get_by_id(session, address_id)
            if not address or str(address.user_id) != user_id:
                return

            await addresses_repo.delete_address(session, address)

    async def set_default(self, user_id: str, address_id: str) -> None:
        """设为默认地址"""
        async with get_pg() as session:
            address = await addresses_repo.get_by_id(session, address_id)
            if not address or str(address.user_id) != user_id:
                raise NotFoundError("地址未找到")

            if not address.is_default:
                await addresses_repo.unset_default_for_user(session, user_id)
                address.is_default = True
                await addresses_repo.update_address(session, address)
