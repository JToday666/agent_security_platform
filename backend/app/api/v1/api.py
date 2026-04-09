from fastapi import APIRouter

from app.shared.http import success_payload
from app.shared.schemas import Envelope, MessagePayload

from app.modules.auth.router import router as auth_router
from app.modules.datasets.router import router as datasets_router
from app.modules.evaluations.router import router as evaluations_router
from app.modules.submissions.router import router as agents_router
from app.modules.user.router import router as user_router

api_router = APIRouter(prefix="/v1", tags=["v1"])
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(datasets_router)
api_router.include_router(agents_router)
api_router.include_router(evaluations_router)

@api_router.get("/", response_model=Envelope[MessagePayload])
async def read_root():
    return success_payload({"message": "API v1!"})
