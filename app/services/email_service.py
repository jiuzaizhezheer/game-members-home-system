import logging

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import NameEmail, SecretStr

from app.core.config import (
    MAIL_FROM,
    MAIL_FROM_NAME,
    MAIL_PASSWORD,
    MAIL_PORT,
    MAIL_SERVER,
    MAIL_SSL_TLS,
    MAIL_STARTTLS,
    MAIL_USERNAME,
    USE_CREDENTIALS,
    VALIDATE_CERTS,
)

logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(MAIL_PASSWORD),
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_STARTTLS=MAIL_STARTTLS,
    MAIL_SSL_TLS=MAIL_SSL_TLS,
    USE_CREDENTIALS=USE_CREDENTIALS,
    VALIDATE_CERTS=VALIDATE_CERTS,
)


class EmailService:
    def __init__(self):
        self.fastmail = FastMail(conf)

    async def send_verification_email(self, email: str, code: str) -> bool:
        """发送注册验证邮件"""
        try:
            html_content = f"""
            <div style="padding: 20px; background-color: #f9f9f9; border-radius: 10px; font-family: sans-serif;">
                <h2 style="color: #333;">Game Members Home</h2>
                <p>您的验证码是：<strong style="color: #4f46e5; font-size: 24px;">{code}</strong></p>
                <p>该验证码在 5 分钟内有效，请勿将验证码泄露给他人。</p>
            </div>
            """

            message = MessageSchema(
                subject="【游戏玩家中心】登录/注册 验证码",
                recipients=[NameEmail(name=email, email=email)],
                body=html_content,
                subtype=MessageType.html,
            )

            await self.fastmail.send_message(message)
            logger.info(f"Successfully sent verification email to {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            return False
