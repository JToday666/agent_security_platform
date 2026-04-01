export interface DatasetSubcategory {
  datasetId: string;
  name: string;
  shortDescription: string;
  sampleCount?: number;
  updatedAt?: string;
  enabled: boolean;
}

export interface DatasetCategory {
  categoryId: string;
  name: string;
  meaning: string;
  description?: string;
  sort: number;
  enabled: boolean;
  subcategoryCount: number;
  subcategories: DatasetSubcategory[];
}

export interface DatasetCategoryViewModel extends DatasetCategory {
  themeIndex: number;
}

export interface DatasetCatalogResponse {
  catalogVersion: string;
  categoryCount: number;
  subcategoryCount: number;
  categories: DatasetCategory[];
}

export interface DatasetMediaItem {
  mediaId: string;
  type: "image" | "video";
  title: string;
  description?: string;
  url: string;
  coverUrl?: string | null;
  sort?: number;
}

export interface DatasetResourceLink {
  label: string;
  url: string;
  type?: "docs" | "download" | "demo";
}

export interface DatasetDetail {
  datasetId: string;
  name: string;
  category: {
    categoryId: string;
    name: string;
    meaning: string;
  };
  shortDescription: string;
  fullDescription: string;
  sampleCount?: number;
  updatedAt?: string;
  highlights: string[];
  scenarios: string[];
  resources: DatasetResourceLink[];
  media: DatasetMediaItem[];
}
