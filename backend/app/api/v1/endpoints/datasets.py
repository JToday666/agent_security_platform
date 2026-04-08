from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.response import fail, success
from app.services.datasets import DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])


def get_dataset_service(db: AsyncSession = Depends(get_db)) -> DatasetService:
    return DatasetService(db)


@router.get("/catalog")
async def get_dataset_catalog(
    service: DatasetService = Depends(get_dataset_service),
):
    try:
        return success(data=await service.get_catalog())
    except HTTPException:
        raise
    except Exception:
        raise fail(status.HTTP_500_INTERNAL_SERVER_ERROR, 50000, "目录加载失败，请稍后重试。")


@router.get("/{datasetId}")
async def get_dataset_detail(
    datasetId: str,
    service: DatasetService = Depends(get_dataset_service),
):
    try:
        return success(data=await service.get_detail(dataset_id=datasetId))
    except HTTPException:
        raise
    except Exception:
        raise fail(status.HTTP_500_INTERNAL_SERVER_ERROR, 50000, "详情加载失败，请重试。")
