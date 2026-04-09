"""数据集模块路由，负责目录与详情查询接口。"""

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
    """返回数据集模块使用的服务实例。"""
    return DatasetService(DatasetRepository(db))


@router.get("/catalog", response_model=Envelope[DatasetCatalogResponse])
async def get_dataset_catalog(service: DatasetService = Depends(get_dataset_service)):
    """返回可用评测项目录。"""
    response = await service.get_catalog()
    return success_payload(response.model_dump(by_alias=True))


@router.get("/{datasetId}", response_model=Envelope[DatasetDetailResponse])
async def get_dataset_detail(datasetId: str, service: DatasetService = Depends(get_dataset_service)):
    """返回指定评测项详情。"""
    response = await service.get_detail(datasetId)
    return success_payload(response.model_dump(by_alias=True))
