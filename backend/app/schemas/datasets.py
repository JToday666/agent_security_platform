from datetime import datetime

from app.schemas.base import CamelModel


class DatasetCatalogItem(CamelModel):
    dataset_id: str
    name: str
    short_description: str | None = None
    sample_count: int
    updated_at: datetime
    enabled: bool


class DatasetCatalogCategory(CamelModel):
    category_id: str
    name: str
    meaning: str | None = None
    description: str | None = None
    sort: int | None = None
    enabled: bool
    subcategory_count: int
    subcategories: list[DatasetCatalogItem]


class DatasetCatalogResponse(CamelModel):
    catalog_version: str
    category_count: int
    subcategory_count: int
    categories: list[DatasetCatalogCategory]


class DatasetCategoryInfo(CamelModel):
    category_id: str
    name: str
    meaning: str | None = None


class DatasetResource(CamelModel):
    label: str
    url: str
    type: str


class DatasetMedia(CamelModel):
    media_id: str
    type: str
    title: str | None = None
    description: str | None = None
    url: str
    cover_url: str | None = None
    sort: int | None = None


class DatasetDetailResponse(CamelModel):
    dataset_id: str
    name: str
    category: DatasetCategoryInfo
    short_description: str | None = None
    full_description: str | None = None
    sample_count: int
    updated_at: datetime
    highlights: list[str]
    scenarios: list[str]
    resources: list[DatasetResource]
    media: list[DatasetMedia]
