export interface DatasetSubcategory {
  datasetId: string;
  name: string;
  shortDescription?: string | null;
  sampleCount?: number | null;
  updatedAt?: string | null;
  enabled: boolean;
}

export interface DatasetCategory {
  categoryId: string;
  name: string;
  meaning?: string | null;
  description?: string | null;
  sort?: number | null;
  enabled: boolean;
  subcategoryCount: number;
  subcategories: DatasetSubcategory[];
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
  description?: string | null;
  url: string;
  coverUrl?: string | null;
  sort?: number | null;
}

export interface DatasetResourceLink {
  label: string;
  url: string;
  type: "docs" | "download" | "demo" | "link";
}

export interface DatasetDistributionItem {
  code: string;
  label: string;
  count: number;
  ratio: number;
}

export interface DatasetSampleProfile {
  deliveryDistribution: DatasetDistributionItem[];
  assetTypeTop: DatasetDistributionItem[];
  difficultyBuckets: DatasetDistributionItem[];
}

export interface DatasetDetail {
  datasetId: string;
  name: string;
  category: {
    categoryId: string;
    name: string;
    meaning?: string | null;
  };
  shortDescription?: string | null;
  fullDescription?: string | null;
  sampleCount?: number | null;
  updatedAt?: string | null;
  highlights: string[];
  scenarios: string[];
  resources: DatasetResourceLink[];
  media: DatasetMediaItem[];
  sampleProfile: DatasetSampleProfile;
}
