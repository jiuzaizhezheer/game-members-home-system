from fastapi import Depends

from app.common.enums import RoleEnum
from app.middleware.security import RoleChecker

# 预定义依赖项
require_member = Depends(RoleChecker(RoleEnum.MEMBER))  # 会员/用户角色依赖
require_merchant = Depends(RoleChecker(RoleEnum.MERCHANT))  # 商户角色依赖
require_admin = Depends(RoleChecker(RoleEnum.ADMIN))  # 管理员角色依赖

require_any_role = Depends(
    RoleChecker(RoleEnum.MEMBER, RoleEnum.MERCHANT, RoleEnum.ADMIN)
)  # 任意角色依赖

require_member_or_merchant = Depends(
    RoleChecker(RoleEnum.MEMBER, RoleEnum.MERCHANT)
)  # 会员或商户角色依赖
