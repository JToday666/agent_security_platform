import type {
  DatasetCategory,
  DatasetSubcategory,
} from "@/shared/types/dataset-types";

export type DatasetCatalogSortKey = "default" | "updated-desc" | "samples-desc";
export const DATASET_CATALOG_ALL_CATEGORY_ID = "__all__";

export interface DatasetCatalogResultItem extends DatasetSubcategory {
  category: DatasetCategory;
}

export interface DatasetCatalogFilterOption {
  categoryId: string;
  name: string;
  count: number;
  sampleCount: number;
  category?: DatasetCategory;
}

export interface DatasetCatalogSummary {
  categoryCount: number;
  datasetCount: number;
  sampleCount: number;
  updatedAt: string | null;
}

const normalizeSearch = (value: string): string => value.trim().toLowerCase();

const normalizeTimestamp = (value?: string | null): number => {
  const parsed = Date.parse(value ?? "");

  return Number.isFinite(parsed) ? parsed : 0;
};

const matchesSearch = (
  item: DatasetCatalogResultItem,
  normalizedSearch: string,
): boolean => {
  if (!normalizedSearch) {
    return true;
  }

  const haystacks = [
    item.name,
    item.shortDescription ?? "",
    item.category.name,
    item.category.meaning ?? "",
    item.category.description ?? "",
  ].map((value) => value.toLowerCase());

  return haystacks.some((value) => value.includes(normalizedSearch));
};

const compareByUpdatedAt = (
  left: DatasetSubcategory,
  right: DatasetSubcategory,
): number =>
  normalizeTimestamp(right.updatedAt) - normalizeTimestamp(left.updatedAt) ||
  left.name.localeCompare(right.name, "zh-CN");

const compareBySampleCount = (
  left: DatasetSubcategory,
  right: DatasetSubcategory,
): number =>
  (right.sampleCount ?? -1) - (left.sampleCount ?? -1) ||
  compareByUpdatedAt(left, right);

const sortDatasets = (
  datasets: DatasetCatalogResultItem[],
  sortKey: DatasetCatalogSortKey,
): DatasetCatalogResultItem[] => {
  if (sortKey === "updated-desc") {
    return [...datasets].sort(compareByUpdatedAt);
  }

  if (sortKey === "samples-desc") {
    return [...datasets].sort(compareBySampleCount);
  }

  return [...datasets];
};

const flattenDatasets = (
  categories: DatasetCategory[],
): DatasetCatalogResultItem[] =>
  categories.flatMap((category) =>
    category.subcategories.map((dataset) => ({
      ...dataset,
      category,
    })),
  );

const sumSamples = (datasets: DatasetSubcategory[]): number =>
  datasets.reduce((total, dataset) => total + (dataset.sampleCount ?? 0), 0);

const resolveLatestUpdatedAt = (
  datasets: DatasetSubcategory[],
): string | null => {
  const latest = datasets.reduce<DatasetSubcategory | null>((current, dataset) => {
    if (!current) {
      return dataset;
    }

    return normalizeTimestamp(dataset.updatedAt) >
      normalizeTimestamp(current.updatedAt)
      ? dataset
      : current;
  }, null);

  return latest?.updatedAt ?? null;
};

const buildFilterOptions = (
  categories: DatasetCategory[],
): DatasetCatalogFilterOption[] => [
  {
    categoryId: DATASET_CATALOG_ALL_CATEGORY_ID,
    name: "all",
    count: categories.reduce(
      (total, category) => total + category.subcategories.length,
      0,
    ),
    sampleCount: sumSamples(flattenDatasets(categories)),
  },
  ...categories.map((category) => ({
    categoryId: category.categoryId,
    name: category.name,
    count: category.subcategories.length,
    sampleCount: sumSamples(category.subcategories),
    category,
  })),
];

export const buildDatasetCatalogView = (
  categories: DatasetCategory[],
  activeCategoryId: string,
  search: string,
  sortKey: DatasetCatalogSortKey,
) => {
  const normalizedSearch = normalizeSearch(search);
  const activeCategory =
    categories.find((category) => category.categoryId === activeCategoryId) ??
    null;
  const scopedCategories = activeCategory ? [activeCategory] : categories;
  const allDatasets = flattenDatasets(categories);
  const scopedDatasets = flattenDatasets(scopedCategories);
  const filteredDatasets = scopedDatasets.filter((dataset) =>
    matchesSearch(dataset, normalizedSearch),
  );
  const sortedDatasets = sortDatasets(filteredDatasets, sortKey);

  return {
    activeCategory,
    activeCategoryId: activeCategory?.categoryId ?? DATASET_CATALOG_ALL_CATEGORY_ID,
    filters: buildFilterOptions(categories),
    results: sortedDatasets,
    resultCount: sortedDatasets.length,
    summary: {
      categoryCount: categories.length,
      datasetCount: allDatasets.length,
      sampleCount: sumSamples(allDatasets),
      updatedAt: resolveLatestUpdatedAt(allDatasets),
    },
  };
};
