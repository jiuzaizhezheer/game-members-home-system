import uuid

import uuid6
from sqlalchemy import Boolean, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class CommunityGroup(BaseEntity):
    __tablename__ = "community_groups"
    __table_args__ = (
        Index("idx_community_groups_merchant", "merchant_id"),
        {"comment": "社群表：社区小组信息"},
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="社群ID",
    )
    merchant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="所属商家ID(可选)",
    )
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="社群名称"
    )
    description: Mapped[str | None] = mapped_column(Text, comment="社群描述")

    member_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default=text("0"), comment="成员数"
    )
    post_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default=text("0"), comment="帖子数"
    )
    cover_image: Mapped[str | None] = mapped_column(String(512), comment="封面图")
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
        comment="是否激活",
    )

    def __repr__(self) -> str:
        return f"CommunityGroup(id={self.id}, name={self.name})"
