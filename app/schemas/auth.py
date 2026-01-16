from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.constants import PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT
from app.common.enums import RoleEnum
from app.utils import id_password_has_letter_and_digit


class AuthRegisterIn(BaseModel):
    username: str = Field(min_length=6, max_length=64, description="用户名")
    email: EmailStr = Field(description="邮箱")
    password: str = Field(
        min_length=6,
        max_length=128,
        description="密码，需包含字母和数字",
    )
    role: RoleEnum = Field(description="角色")
    captcha_id: str = Field(min_length=36, max_length=36, description="验证码ID")
    captcha_code: str = Field(min_length=6, max_length=6, description="验证码文本")

    @field_validator("password")
    @classmethod
    def _password_has_letter_and_digit(cls, v: str) -> str:
        if not id_password_has_letter_and_digit(v):
            raise ValueError(PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT)
        return v


class AuthLoginIn(BaseModel):
    email: EmailStr = Field(description="邮箱")
    password: str = Field(description="密码")
    role: RoleEnum = Field(description="角色")


class CaptchaOut(BaseModel):
    id: str = Field(description="验证码唯一标识")
    image: str = Field(description="base64 编码后的图片数据")


class TokenOut(BaseModel):
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")


class AccessTokenOut(BaseModel):
    access_token: str = Field(description="访问令牌")
