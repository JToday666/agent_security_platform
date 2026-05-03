"""数据集模块请求与响应模型。"""

from app.platform.schemas import CamelModel


class DatasetCatalogItem(CamelModel):
    """目录中单个评测项的摘要信息。"""

    dataset_id: str
    name: str
    short_description: str | None = None
    sample_count: int
    updated_at: str
    enabled: bool


class DatasetCatalogCategory(CamelModel):
    """目录中的风险分类分组。"""

    category_id: str
    name: str
    meaning: str | None = None
    description: str | None = None
    sort: int | None = None
    enabled: bool
    subcategory_count: int
    subcategories: list[DatasetCatalogItem]


class DatasetCatalogResponse(CamelModel):
    """数据集目录接口响应体。"""

    catalog_version: str
    category_count: int
    subcategory_count: int
    categories: list[DatasetCatalogCategory]


class DatasetCategoryInfo(CamelModel):
    """数据集详情中的分类信息。"""

    category_id: str
    name: str
    meaning: str | None = None


class DatasetDetailResponse(CamelModel):
    """数据集详情接口响应体。"""

    dataset_id: str
    name: str
    category: DatasetCategoryInfo
    short_description: str | None = None
    full_description: str | None = None
    sample_count: int
    updated_at: str
    highlights: list[str]
    scenarios: list[str]
    resources: list[dict[str, object]]
    media: list[dict[str, object]]
