"""FastAPI 应用入口，负责初始化共享能力并挂载顶层路由。"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.platform.config import settings
from app.platform.exception_handlers import register_exception_handlers
from app.platform.http import success_payload
from app.platform.runtime import ensure_runtime_dirs

app = FastAPI(title=settings.PROJECT_NAME)

ensure_runtime_dirs()
register_exception_handlers(app)
app.mount("/uploads", StaticFiles(directory=settings.uploads_root), name="uploads")

app.include_router(api_router)


@app.get("/")
async def read_root():
    """返回服务根路径的欢迎信息。"""
    return success_payload({"message": f"Hello FastAPI project! PROJECT_NAME: {settings.PROJECT_NAME}"})
