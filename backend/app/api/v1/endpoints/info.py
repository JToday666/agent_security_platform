from fastapi import APIRouter

from app.core.config import settings
from app.schemas.info import InfoResponse

router = APIRouter()


@router.get("/info", response_model=InfoResponse)
async def service_info() -> InfoResponse:
    return InfoResponse(
        service=settings.project_name,
        environment=settings.environment,
    )
