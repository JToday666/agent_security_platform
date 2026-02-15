from fastapi import APIRouter
from .v1.api import api_router as api_v1_router

api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(api_v1_router)
@api_router.get("/")
async def read_root():
    return {"message": "Welcome to the API!"}
