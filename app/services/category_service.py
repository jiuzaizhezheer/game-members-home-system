"""分类服务层：分类业务逻辑"""

from app.database import get_db
from app.repo import categories_repo
from app.schemas.category import CategoryOut


class CategoryService:
    """分类服务"""

    async def get_all_categories(self) -> list[CategoryOut]:
        """获取所有分类列表"""
        async with get_db() as session:
            categories = await categories_repo.get_all(session)
            return [CategoryOut.model_validate(c) for c in categories]
