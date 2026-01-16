from pydantic import BaseModel, Field


class CaptchaOut(BaseModel):
    id: str = Field(description="验证码唯一标识")
    image: str = Field(description="base64 编码后的图片数据")


class TokenOut(BaseModel):
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")


class AccessTokenOut(BaseModel):
    access_token: str = Field(description="访问令牌")
