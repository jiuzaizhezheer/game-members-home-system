import base64
import random
import string
import uuid

from app.redis import get_redis
from app.schemas.auth import CaptchaOut


class CaptchaService:
    CAPTCHA_PREFIX = "captcha:"
    EXPIRE_SECONDS = 60

    def _random_code(self, length: int = 6) -> str:
        """生成随机验证码文本（大写字母 + 数字）"""
        alphabet = string.ascii_uppercase + (string.digits * 3)
        return "".join(random.choice(alphabet) for _ in range(length))

    def _build_svg(self, text: str, width: int = 120, height: int = 40) -> str:
        """构造包含验证码文本的 SVG 图片"""
        noise_lines = []
        for _ in range(3):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            color = f"#{random.randint(0, 0xFFFFFF):06x}"
            noise_lines.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1"/>'
            )

        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            f'<rect width="100%" height="100%" fill="#f4f5f7"/>'
            + "".join(noise_lines)
            + f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="22" font-family="monospace" fill="#333">{text}</text>'
            + "</svg>"
        )
        return svg

    async def create_captcha(self) -> CaptchaOut:
        """
        生成验证码
        Returns:
            {
                "id": str,
                "image": str (base64 svg)
            }
        """
        code = self._random_code()
        captcha_id = str(uuid.uuid4())

        svg = self._build_svg(text=code)
        encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        image_data = f"data:image/svg+xml;base64,{encoded}"

        key = f"{self.CAPTCHA_PREFIX}{captcha_id}"
        async with get_redis() as redis:
            await redis.setex(key, self.EXPIRE_SECONDS, code.lower())

        return CaptchaOut(id=captcha_id, image=image_data)

    async def verify_captcha(self, captcha_id: str, code: str) -> bool:
        """
        验证验证码
        验证成功后会删除 Redis 中的记录（防止重放）
        """
        if not captcha_id or not code:
            return False

        key = f"{self.CAPTCHA_PREFIX}{captcha_id}"
        async with get_redis() as redis:
            stored_code = await redis.get(key)

            if not stored_code:
                return False

            if stored_code == code.strip().lower():
                await redis.delete(key)
                return True

            return False
