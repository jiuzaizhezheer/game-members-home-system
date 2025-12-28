import asyncio

import pytest

from app.services.captcha_service import CaptchaService


@pytest.mark.asyncio(loop_scope="session")
async def test_captcha_flow():
    print("开始测试验证码流程...")
    service = CaptchaService()

    # 1. 生成验证码
    print("\n[Step 1] 生成验证码...")
    result = await service.create_captcha()
    captcha_id = result["id"]
    image_base64 = result["image"]

    print(f"Captcha ID: {captcha_id}")
    print(f"Image length: {len(image_base64)}")
    assert captcha_id
    assert "data:image/svg+xml;base64," in image_base64

    # 获取真实的 code (仅用于测试，实际业务中前端不知道)
    # 通过私有方法访问 Redis 获取 code，模拟用户识别图片
    from app.redis import get_redis

    async with get_redis() as r:
        real_code = await r.get(f"captcha:{captcha_id}")
    print(f"Real Code (from Redis): {real_code}")

    # 2. 验证错误的验证码
    print("\n[Step 2] 验证错误的验证码...")
    is_valid = await service.verify_captcha(captcha_id, "wrong_code")
    print(f"Verify 'wrong_code': {is_valid}")
    assert is_valid is False

    # 3. 验证正确的验证码
    print("\n[Step 3] 验证正确的验证码...")
    is_valid = await service.verify_captcha(captcha_id, real_code)
    print(f"Verify '{real_code}': {is_valid}")
    assert is_valid is True

    # 4. 验证防重放（再次使用同一个验证码）
    print("\n[Step 4] 验证防重放...")
    is_valid = await service.verify_captcha(captcha_id, real_code)
    print(f"Verify again: {is_valid}")
    assert is_valid is False

    print("\n所有测试通过！")

    # 等待连接释放
    await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(test_captcha_flow())
