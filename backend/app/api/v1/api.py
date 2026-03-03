from fastapi import APIRouter
from .endpoints.auth import router as auth_router
from .endpoints.user import router as user_router

api_router = APIRouter(prefix="/v1", tags=["v1"])
api_router.include_router(auth_router)
api_router.include_router(user_router)

@api_router.get("/")
async def read_root():
    return {"message": "API v1!"}
