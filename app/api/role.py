from fastapi import Depends

from app.common.enums import RoleEnum
from app.middleware.security import RoleChecker

# 预定义依赖项
require_member = Depends(RoleChecker(RoleEnum.MEMBER))
require_merchant = Depends(RoleChecker(RoleEnum.MERCHANT))
require_admin = Depends(RoleChecker(RoleEnum.ADMIN))
