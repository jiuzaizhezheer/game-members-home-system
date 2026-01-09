import uuid

import uuid6
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class CommunityGroup(Base, TimestampMixin):
    __tablename__ = "community_groups"
    __table_args__ = {"comment": "社群表：社区小组信息"}
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="社群ID",
    )
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="社群名称"
    )
    description: Mapped[str | None] = mapped_column(Text, comment="社群描述")

    def __repr__(self) -> str:
        return f"CommunityGroup(id={self.id}, name={self.name})"
