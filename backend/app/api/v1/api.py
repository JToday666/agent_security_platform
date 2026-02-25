from fastapi import APIRouter
from .endpoints.test1 import router as test1_router
from .endpoints.test2 import router as test2_router

api_router = APIRouter(prefix="/v1", tags=["v1"])
api_router.include_router(test1_router)
api_router.include_router(test2_router)

@api_router.get("/")
async def read_root():
    return {"message": "API v1!"}
