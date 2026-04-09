from app.shared.schemas import CamelModel


class DatasetCatalogItem(CamelModel):
    dataset_id: str
    name: str
    short_description: str | None = None
    sample_count: int
    updated_at: str
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


class DatasetDetailResponse(CamelModel):
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
