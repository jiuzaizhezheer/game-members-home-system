import argparse
import asyncio

from app.common.enums import RoleEnum
from app.database.pgsql import get_pg
from app.entity.pgsql import User
from app.repo import users_repo
from app.utils import hash_password, id_password_has_letter_and_digit


async def create_admin(username, email, password):
    """
    专门用于创建系统管理员的脚本
    """
    role_val = RoleEnum.ADMIN

    # 基础校验 (参照 AuthRegisterIn Schema 的约束)
    if len(username) < 6 or len(username) > 64:
        print(f"❌ 错误: 用户名长度必须在 6-64 之间 (当前: {len(username)})")
        return

    if len(password) < 6 or len(password) > 128:
        print(f"❌ 错误: 密码长度必须在 6-128 之间 (当前: {len(password)})")
        return

    if not id_password_has_letter_and_digit(password):
        print("❌ 错误: 密码必须包含字母和数字")
        return

    print(f"🚀 正在初始化系统管理员: {username} ({email})...")

    async with get_pg() as session:
        # 1. 检查是否存在
        exists = await users_repo.exists_by_username_or_email_in_role(
            session, username, email, role_val
        )
        if exists:
            print("❌ 错误: 用户名或邮箱在 [管理员] 角色下已存在")
            return

        # 2. 创建管理员实体
        user = User(
            username=username,
            email=email,
            role=role_val,
            password_hash=hash_password(password),
        )
        await users_repo.create(session, user)
        print(f"✅ 管理员账号创建成功, ID: {user.id}")


def main():
    parser = argparse.ArgumentParser(description="系统管理员初始化工具")
    parser.add_argument("--username", required=True, help="管理员用户名 (至少6位)")
    parser.add_argument("--email", required=True, help="管理员邮箱")
    parser.add_argument(
        "--password", required=True, help="登录密码 (至少6位，包含字母和数字)"
    )

    args = parser.parse_args()

    try:
        asyncio.run(create_admin(args.username, args.email, args.password))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n❌ 执行过程中发生非预期错误: {e}")


if __name__ == "__main__":
    main()
