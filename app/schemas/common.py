"""通用相关的请求和响应模型"""

from pydantic import BaseModel, Field


class FileUploadOut(BaseModel):
    """文件上传响应"""

    url: str = Field(description="文件访问URL")
