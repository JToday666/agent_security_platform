from fastapi import APIRouter

from app.shared.http import success_payload
from app.shared.schemas import Envelope, MessagePayload
from .v1.api import api_router as api_v1_router

api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(api_v1_router)

@api_router.get("/", response_model=Envelope[MessagePayload])
async def read_root():
    return success_payload({"message": "Welcome to the API!"})
