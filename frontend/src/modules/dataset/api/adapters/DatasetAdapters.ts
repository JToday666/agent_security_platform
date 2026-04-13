import type {
  SubmitAgentApiPayload,
  SubmitAgentPayload,
} from "@/shared/types/AgentTypes";
import type {
  DatasetCatalogResponse,
  DatasetDetail,
  DatasetCatalogResponse as FrontendDatasetCatalogResponse,
  DatasetDetail as FrontendDatasetDetail,
  DatasetMediaItem,
  DatasetResourceLink,
} from "@/shared/types/DatasetTypes";
import { normalizeApiAssetUrl } from "@/shared/api/ApiRuntime";

type UnknownRecord = Record<string, unknown>;

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
    `相关资源 ${index + 1}`;
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
    title: toStringValue(candidate.title) || `媒体 ${index + 1}`,
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
  left: FrontendDatasetCatalogResponse["categories"][number],
  right: FrontendDatasetCatalogResponse["categories"][number],
): number =>
  toNumberValue(left.sort, Number.MAX_SAFE_INTEGER) -
    toNumberValue(right.sort, Number.MAX_SAFE_INTEGER) ||
  left.categoryId.localeCompare(right.categoryId);

export const buildSubmitAgentApiPayload = (
  payload: SubmitAgentPayload,
): SubmitAgentApiPayload => ({
  agentName: payload.agentName,
  description: payload.description,
  submitMethod: payload.submitMethod,
  api: payload.api,
  docker: payload.docker,
  parameters: payload.parameters,
  publicToLeaderboard: payload.publicToLeaderboard,
  requestId: payload.requestId,
  datasetIds: payload.selectedDatasetIds,
});

export const adaptDatasetCatalog = (
  payload: DatasetCatalogResponse,
): FrontendDatasetCatalogResponse => {
  const categories = Array.isArray(payload?.categories)
    ? payload.categories
    : [];

  const normalizedCategories = categories
    .map((category) => ({
      categoryId: toStringValue(category.categoryId),
      name: toStringValue(category.name) || "未命名分类",
      meaning: toOptionalString(category.meaning),
      description: toOptionalString(category.description),
      sort: category.sort == null ? null : toNumberValue(category.sort),
      enabled: toBooleanValue(category.enabled, true),
      subcategoryCount: Array.isArray(category.subcategories)
        ? category.subcategories.length
        : 0,
      subcategories: (Array.isArray(category.subcategories)
        ? category.subcategories
        : []
      ).map((dataset) => ({
        datasetId: toStringValue(dataset.datasetId),
        name: toStringValue(dataset.name) || "未命名评测项",
        shortDescription: toOptionalString(dataset.shortDescription),
        sampleCount:
          dataset.sampleCount == null
            ? null
            : toNumberValue(dataset.sampleCount),
        updatedAt: toOptionalString(dataset.updatedAt),
        enabled: toBooleanValue(dataset.enabled, true),
      })),
    }))
    .filter((category) => category.categoryId.length > 0)
    .sort(sortDatasetCategories);

  return {
    catalogVersion: toStringValue(payload?.catalogVersion) || "",
    categoryCount: normalizedCategories.length,
    subcategoryCount: normalizedCategories.reduce(
      (total, category) => total + category.subcategories.length,
      0,
    ),
    categories: normalizedCategories,
  };
};

export const adaptDatasetDetail = (
  payload: DatasetDetail,
): FrontendDatasetDetail => {
  const category = payload?.category ?? {
    categoryId: "",
    name: "",
    meaning: null,
  };

  return {
    datasetId: toStringValue(payload?.datasetId),
    name: toStringValue(payload?.name) || "未命名评测项",
    category: {
      categoryId: toStringValue(category.categoryId),
      name: toStringValue(category.name) || "未分类",
      meaning: toOptionalString(category.meaning),
    },
    shortDescription: toOptionalString(payload?.shortDescription),
    fullDescription: toOptionalString(payload?.fullDescription),
    sampleCount:
      payload?.sampleCount == null ? null : toNumberValue(payload.sampleCount),
    updatedAt: toOptionalString(payload?.updatedAt),
    highlights: toStringArray(payload?.highlights),
    scenarios: toStringArray(payload?.scenarios),
    resources: (Array.isArray(payload?.resources) ? payload.resources : [])
      .map((resource, index) => normalizeResource(resource, index))
      .filter((resource): resource is DatasetResourceLink => resource !== null),
    media: (Array.isArray(payload?.media) ? payload.media : [])
      .map((media, index) => normalizeMedia(media, index))
      .filter((media): media is DatasetMediaItem => media !== null),
  };
};
