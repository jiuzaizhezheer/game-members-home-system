from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_routers
from app.core.lifespan import lifespan
from app.middleware.exception_handlers import register_exception_handlers

app = FastAPI(
    lifespan=lifespan,
    title="游戏会员之家系统",
    version="1.0.0",
    description="游戏会员之家系统",
)

# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO 允许所有源，开发阶段可以先这样设置
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_routers)
register_exception_handlers(app)


# 健康检查路由
@app.get(path="/healthy", status_code=status.HTTP_200_OK, tags=["healthy"])
async def healthy():
    return {"status": "ok"}
