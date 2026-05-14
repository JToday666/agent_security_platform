import type {
  DatasetCatalogResponse,
  DatasetDetail,
  DatasetMediaItem,
  DatasetResourceLink,
} from "@/shared/types/dataset-types";
import { normalizeApiAssetUrl } from "@/shared/api/api-runtime";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";

type UnknownRecord = Record<string, unknown>;

const toRecord = (value: unknown): UnknownRecord =>
  value && typeof value === "object" ? (value as UnknownRecord) : {};

const toStringValue = (value: unknown): string =>
  typeof value === "string" ? value.trim() : "";

const toOptionalString = (value: unknown): string | null => {
  const normalized = toStringValue(value);
  return normalized ? normalized : null;
};

const toNumberValue = (value: unknown, fallback = 0): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const toBooleanValue = (value: unknown, fallback = false): boolean =>
  typeof value === "boolean" ? value : fallback;

const toStringArray = (value: unknown): string[] =>
  Array.isArray(value)
    ? value.map((item) => toStringValue(item)).filter((item) => item.length > 0)
    : [];

const normalizeResource = (
  resource: unknown,
  index: number,
): DatasetResourceLink | null => {
  if (!resource || typeof resource !== "object") {
    return null;
  }

  const candidate = resource as UnknownRecord;
  const label =
    toStringValue(candidate.label) ||
    toStringValue(candidate.title) ||
    translateRuntimeMessage("dataset.fallback.relatedResource", {
      index: index + 1,
    });
  const url = normalizeApiAssetUrl(toOptionalString(candidate.url));
  if (!url) {
    return null;
  }

  const type = toStringValue(candidate.type);
  return {
    label,
    url,
    type:
      type === "docs" || type === "download" || type === "demo" ? type : "link",
  };
};

const normalizeMedia = (
  media: unknown,
  index: number,
): DatasetMediaItem | null => {
  if (!media || typeof media !== "object") {
    return null;
  }

  const candidate = media as UnknownRecord;
  const url = normalizeApiAssetUrl(toOptionalString(candidate.url));
  const type = toStringValue(candidate.type);
  if (!url || (type !== "image" && type !== "video")) {
    return null;
  }

  return {
    mediaId:
      toStringValue(candidate.mediaId) ||
      toStringValue(candidate.id) ||
      `media-${index + 1}`,
    type,
    title:
      toStringValue(candidate.title) ||
      translateRuntimeMessage("dataset.fallback.media", { index: index + 1 }),
    description: toOptionalString(candidate.description),
    url,
    coverUrl: normalizeApiAssetUrl(
      toOptionalString(candidate.coverUrl) ??
        toOptionalString(candidate.poster),
    ),
    sort: candidate.sort == null ? null : toNumberValue(candidate.sort, index),
  };
};

const sortDatasetCategories = (
  left: DatasetCatalogResponse["categories"][number],
  right: DatasetCatalogResponse["categories"][number],
): number =>
  toNumberValue(left.sort, Number.MAX_SAFE_INTEGER) -
    toNumberValue(right.sort, Number.MAX_SAFE_INTEGER) ||
  left.categoryId.localeCompare(right.categoryId);

export const adaptDatasetCatalog = (
  payload: unknown,
): DatasetCatalogResponse => {
  const candidate = toRecord(payload);
  const categories = Array.isArray(candidate.categories)
    ? candidate.categories
    : [];

  const normalizedCategories = categories
    .map((value) => {
      const category = toRecord(value);
      const subcategories = Array.isArray(category.subcategories)
        ? category.subcategories
        : [];

      return {
        categoryId: toStringValue(category.categoryId),
        name:
          toStringValue(category.name) ||
          translateRuntimeMessage("dataset.fallback.unnamedCategory"),
        meaning: toOptionalString(category.meaning),
        description: toOptionalString(category.description),
        sort: category.sort == null ? null : toNumberValue(category.sort),
        enabled: toBooleanValue(category.enabled, true),
        subcategoryCount: subcategories.length,
        subcategories: subcategories.map((value) => {
          const dataset = toRecord(value);

          return {
            datasetId: toStringValue(dataset.datasetId),
            name:
              toStringValue(dataset.name) ||
              translateRuntimeMessage("dataset.fallback.unnamedBenchmarkItem"),
            shortDescription: toOptionalString(dataset.shortDescription),
            sampleCount:
              dataset.sampleCount == null
                ? null
                : toNumberValue(dataset.sampleCount),
            updatedAt: toOptionalString(dataset.updatedAt),
            enabled: toBooleanValue(dataset.enabled, true),
          };
        }),
      };
    })
    .filter((category) => category.categoryId.length > 0)
    .sort(sortDatasetCategories);

  return {
    catalogVersion: toStringValue(candidate.catalogVersion) || "",
    categoryCount: normalizedCategories.length,
    subcategoryCount: normalizedCategories.reduce(
      (total, category) => total + category.subcategories.length,
      0,
    ),
    categories: normalizedCategories,
  };
};

export const adaptDatasetDetail = (payload: unknown): DatasetDetail => {
  const candidate = toRecord(payload);
  const category = toRecord(candidate.category);

  return {
    datasetId: toStringValue(candidate.datasetId),
    name:
      toStringValue(candidate.name) ||
      translateRuntimeMessage("dataset.fallback.unnamedBenchmarkItem"),
    category: {
      categoryId: toStringValue(category.categoryId),
      name:
        toStringValue(category.name) ||
        translateRuntimeMessage("dataset.fallback.uncategorized"),
      meaning: toOptionalString(category.meaning),
    },
    shortDescription: toOptionalString(candidate.shortDescription),
    fullDescription: toOptionalString(candidate.fullDescription),
    sampleCount:
      candidate.sampleCount == null
        ? null
        : toNumberValue(candidate.sampleCount),
    updatedAt: toOptionalString(candidate.updatedAt),
    highlights: toStringArray(candidate.highlights),
    scenarios: toStringArray(candidate.scenarios),
    resources: (Array.isArray(candidate.resources) ? candidate.resources : [])
      .map((resource, index) => normalizeResource(resource, index))
      .filter((resource): resource is DatasetResourceLink => resource !== null),
    media: (Array.isArray(candidate.media) ? candidate.media : [])
      .map((media, index) => normalizeMedia(media, index))
      .filter((media): media is DatasetMediaItem => media !== null),
  };
};
