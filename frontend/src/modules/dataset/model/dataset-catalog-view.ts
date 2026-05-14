import type {
  DatasetCategory,
  DatasetSubcategory,
} from "@/shared/types/dataset-types";

export type DatasetCatalogSortKey = "default" | "updated-desc" | "samples-desc";

const normalizeSearch = (value: string): string => value.trim().toLowerCase();

const matchesSearch = (
  dataset: DatasetSubcategory,
  normalizedSearch: string,
): boolean => {
  if (!normalizedSearch) {
    return true;
  }

  const haystacks = [dataset.name, dataset.shortDescription ?? ""].map((item) =>
    item.toLowerCase(),
  );

  return haystacks.some((item) => item.includes(normalizedSearch));
};

const compareByUpdatedAt = (
  left: DatasetSubcategory,
  right: DatasetSubcategory,
): number =>
  Date.parse(right.updatedAt ?? "") - Date.parse(left.updatedAt ?? "") ||
  left.name.localeCompare(right.name, "zh-CN");

const compareBySampleCount = (
  left: DatasetSubcategory,
  right: DatasetSubcategory,
): number =>
  (right.sampleCount ?? -1) - (left.sampleCount ?? -1) ||
  compareByUpdatedAt(left, right);

const sortDatasets = (
  datasets: DatasetSubcategory[],
  sortKey: DatasetCatalogSortKey,
): DatasetSubcategory[] => {
  if (sortKey === "updated-desc") {
    return [...datasets].sort(compareByUpdatedAt);
  }

  if (sortKey === "samples-desc") {
    return [...datasets].sort(compareBySampleCount);
  }

  return [...datasets];
};

export const buildDatasetCatalogView = (
  category: DatasetCategory,
  search: string,
  sortKey: DatasetCatalogSortKey,
) => {
  const normalizedSearch = normalizeSearch(search);
  const filteredDatasets = category.subcategories.filter((dataset) =>
    matchesSearch(dataset, normalizedSearch),
  );
  const sortedDatasets = sortDatasets(filteredDatasets, sortKey);

  return {
    category: {
      ...category,
      subcategories: sortedDatasets,
      subcategoryCount: sortedDatasets.length,
    },
    resultCount: sortedDatasets.length,
  };
};
