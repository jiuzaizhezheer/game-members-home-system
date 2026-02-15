import os
import shutil
import uuid
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.schemas import FileUploadOut, SuccessResponse

common_router = APIRouter()

# 获取上传目录
UPLOAD_DIR = os.path.join(os.getcwd(), "static", "uploads")


@common_router.post(
    path="/upload",
    response_model=SuccessResponse[FileUploadOut],
    status_code=status.HTTP_201_CREATED,
    tags=["upload"],
)
async def upload_file(
    file: Annotated[UploadFile, File(description="上传的文件")]
) -> SuccessResponse[FileUploadOut]:
    """通用文件上传接口"""
    # 确保文件夹存在
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 生成唯一文件名
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # 保存文件
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 生成访问 URL
    # 这里假设前端能通过 /static 访问到，具体的映射取决于 main.py 的 mount 配置
    url = f"/static/uploads/{filename}"

    return SuccessResponse[FileUploadOut](
        message="上传成功", data=FileUploadOut(url=url)
    )
