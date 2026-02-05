from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging(settings.log_level)
app = FastAPI(title=settings.project_name)
app.include_router(api_router, prefix=settings.api_v1_str)

@app.get("/")
async def read_root():
    return {"message": "Hello from FastAPI!"}
