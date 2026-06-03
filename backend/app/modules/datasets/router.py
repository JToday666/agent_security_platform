"""攻击场景库路由，负责目录与评测项详情查询接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.datasets.repository import DatasetRepository
from app.modules.datasets.schemas import DatasetCatalogResponse, DatasetDetailResponse
from app.modules.datasets.service import DatasetService
from app.platform.auth import get_db
from app.platform.http import success_payload
from app.platform.schemas import Envelope

router = APIRouter(prefix="/attack-scenarios", tags=["attack-scenarios"])


def get_dataset_service(db: AsyncSession = Depends(get_db)) -> DatasetService:
    """返回数据集模块使用的服务实例。"""
    return DatasetService(DatasetRepository(db))


@router.get("/catalog", response_model=Envelope[DatasetCatalogResponse])
async def get_attack_scenario_catalog(
    service: DatasetService = Depends(get_dataset_service),
):
    """返回可用攻击场景库目录。"""
    response = await service.get_catalog()
    return success_payload(response.model_dump(by_alias=True))


@router.get(
    "/evaluation-items/{evaluationItemId}",
    response_model=Envelope[DatasetDetailResponse],
)
async def get_evaluation_item_detail(
    evaluationItemId: str, service: DatasetService = Depends(get_dataset_service)
):
    """返回指定评测项详情。"""
    response = await service.get_detail(evaluationItemId)
    return success_payload(response.model_dump(by_alias=True))
