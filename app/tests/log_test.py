import uvicorn
from fastapi import FastAPI

from app.common.errors import DuplicateResourceError

app = FastAPI()


@app.get("/")
async def root():
    # 模拟抛出继承自 HTTPException 的异常
    raise DuplicateResourceError("测试异常日志")


if __name__ == "__main__":
    uvicorn.run(app, port=8001)
