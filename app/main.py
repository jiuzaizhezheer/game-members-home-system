from fastapi import FastAPI

from app.api.router import api_router
from app.core.lifespan import lifespan
from app.middleware.exception_handlers import register_exception_handlers

app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
register_exception_handlers(app)


@app.get("/healthy", tags=["healthy"])
async def healthy():
    return {"status": "ok"}
