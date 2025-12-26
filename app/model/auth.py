import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.constants import PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT


class RegisterRequest(BaseModel):
    username: str = Field(min_length=5, max_length=64, description="用户名")
    email: EmailStr = Field(description="邮箱")
    password: str = Field(
        min_length=6,
        max_length=128,
        description="密码，需包含字母和数字",
    )
    role: str = Field(pattern=r"^(member|merchant|admin)$", description="角色")
    captcha_id: str = Field(min_length=36, max_length=36, description="验证码ID")
    captcha_code: str = Field(min_length=6, max_length=6, description="验证码文本")

    @field_validator("password")
    def _password_has_letter_and_digit(v: str) -> str:
        if re.search(r"[A-Za-z]", v) is None or re.search(r"\d", v) is None:
            raise ValueError(PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT)
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)
