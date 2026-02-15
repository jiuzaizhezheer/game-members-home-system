import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.common.constants import (
    NEW_PASSWORD_SAME_AS_OLD,
    PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT,
)
from app.common.enums import RoleEnum
from app.utils import id_password_has_letter_and_digit


class UserChangePasswordIn(BaseModel):
    old_password: str = Field(description="旧密码")
    new_password: str = Field(
        min_length=6,
        max_length=128,
        description="新密码，需包含字母和数字",
    )

    @field_validator("new_password")
    @classmethod
    def _password_has_letter_and_digit(cls, v: str) -> str:
        if not id_password_has_letter_and_digit(v):
            raise ValueError(PASSWORD_MUST_CONTAIN_LETTER_AND_DIGIT)
        return v

    @model_validator(mode="after")
    def _check_passwords_match(self):
        if self.old_password == self.new_password:
            raise ValueError(NEW_PASSWORD_SAME_AS_OLD)
        return self


class UserOut(BaseModel):
    id: uuid.UUID = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: EmailStr = Field(description="邮箱")
    role: RoleEnum = Field(description="角色")
    avatar_url: str | None = Field(description="头像地址")
    created_at: datetime = Field(description="创建时间")

    model_config = {"from_attributes": True}


class UserProfileUpdateIn(BaseModel):
    username: str | None = Field(default=None, description="用户名")
    avatar_url: str | None = Field(default=None, description="头像地址")
    email: EmailStr | None = Field(default=None, description="邮箱")
