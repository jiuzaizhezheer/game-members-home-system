from pydantic import ValidationError

from app.schemas import AuthRegisterIn
from app.core.config import RoleEnum

try:
    # 测试正确的情况
    print("Testing valid input...")
    AuthRegisterIn(
        username="validuser",
        email="test@example.com",
        password="password123",
        role=RoleEnum.member,
        captcha_id="a" * 36,
        captcha_code="123456",
    )
    print("Valid input passed.")

    # 测试 captcha_id 长度过长
    print("\nTesting invalid captcha_id length (too long)...")
    try:
        AuthRegisterIn(
            username="validuser",
            email="test@example.com",
            password="password123",
            role=RoleEnum.member,
            captcha_id="a" * 37,  # 长度太长
            captcha_code="123456",
        )
    except ValidationError as e:
        print(f"Caught expected error for captcha_id: {e}")

    # 测试 captcha_code 长度过长
    print("\nTesting invalid captcha_code length (too long)...")
    try:
        AuthRegisterIn(
            username="validuser",
            email="test@example.com",
            password="password123",
            role=RoleEnum.member,
            captcha_id="a" * 36,
            captcha_code="1234567",  # 长度太长
        )
    except ValidationError as e:
        print(f"Caught expected error for captcha_code: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
