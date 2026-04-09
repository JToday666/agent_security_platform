from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.schemas import DatasetCatalogResponse, DatasetDetailResponse
from app.modules.datasets.service import DatasetService
from app.shared.auth import get_db
from app.shared.http import success_payload
from app.shared.schemas import Envelope

router = APIRouter(prefix="/datasets", tags=["datasets"])


def get_dataset_service(db: AsyncSession = Depends(get_db)) -> DatasetService:
    return DatasetService(DatasetRepository(db))


@router.get("/catalog", response_model=Envelope[DatasetCatalogResponse])
async def get_dataset_catalog(service: DatasetService = Depends(get_dataset_service)):
    response = await service.get_catalog()
    return success_payload(response.model_dump(by_alias=True))


@router.get("/{datasetId}", response_model=Envelope[DatasetDetailResponse])
async def get_dataset_detail(datasetId: str, service: DatasetService = Depends(get_dataset_service)):
    response = await service.get_detail(datasetId)
    return success_payload(response.model_dump(by_alias=True))
