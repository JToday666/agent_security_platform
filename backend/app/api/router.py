"""聚合 `/api` 前缀下的版本化接口路由。"""

from fastapi import APIRouter

from app.platform.http import success_payload
from app.platform.schemas import Envelope, MessagePayload
from .v1.api import api_router as api_v1_router

api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(api_v1_router)


@api_router.get("/", response_model=Envelope[MessagePayload])
async def read_root():
    """返回 API 根路径的基础说明。"""
    return success_payload({"message": "Welcome to the API!"})
