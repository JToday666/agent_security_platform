"""FastAPI 应用入口，负责初始化共享能力并挂载顶层路由。"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.router import api_router
from app.modules.runtime_gateway.router import router as runtime_gateway_router
from app.platform.config import settings
from app.platform.db.session import AsyncSessionLocal
from app.platform.exception_handlers import register_exception_handlers
from app.platform.http import json_error_response, success_payload
from app.platform.i18n import LocaleMiddleware
from app.platform.logging import configure_logging
from app.platform.runtime import ensure_runtime_dirs

configure_logging()

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(LocaleMiddleware)
ensure_runtime_dirs()
register_exception_handlers(app)
app.mount("/uploads", StaticFiles(directory=settings.uploads_root), name="uploads")

app.include_router(api_router)
app.include_router(runtime_gateway_router)


@app.get("/")
async def read_root():
    """返回服务根路径的欢迎信息。"""
    return success_payload(
        {"message": f"Hello FastAPI project! PROJECT_NAME: {settings.PROJECT_NAME}"}
    )


@app.get("/healthz")
async def healthz():
    """Return a lightweight liveness probe response."""
    return success_payload({"status": "ok"})


@app.get("/readyz")
async def readyz():
    """Return readiness only when the database is reachable."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("select 1"))
    except Exception:
        return json_error_response(
            http_status=503,
            code=50300,
            message="service not ready",
            data={"status": "not_ready"},
        )
    return success_payload({"status": "ready"})
