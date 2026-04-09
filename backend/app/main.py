from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.shared.config import settings
from app.shared.exception_handlers import register_exception_handlers
from app.shared.http import success_payload
from app.shared.runtime import ensure_runtime_dirs

app = FastAPI(title=settings.PROJECT_NAME)

ensure_runtime_dirs()
register_exception_handlers(app)
app.mount("/uploads", StaticFiles(directory=settings.uploads_root), name="uploads")

app.include_router(api_router)


@app.get("/")
async def read_root():
    return success_payload({"message": f"Hello FastAPI project! PROJECT_NAME: {settings.PROJECT_NAME}"})
