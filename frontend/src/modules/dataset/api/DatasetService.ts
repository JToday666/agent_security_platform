import request from "@/shared/api/HttpClient";
import { ApiConfig } from "@/shared/api/Config";
import {
  readMemoryCache,
  setMemoryCache,
  withMemoryCache,
} from "@/shared/api/MemoryCache";
import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
  shouldMockFail,
} from "@/shared/api/MockApiUtils";
import {
  adaptDatasetCatalog,
  adaptDatasetDetail,
} from "@/modules/dataset/api/adapters/DatasetAdapters";
import {
  buildReferenceDatasetCatalog,
  getReferenceDatasetDetail,
} from "@/modules/dataset/mock/DatasetFixtures";
import { normalizeDatasetId } from "@/modules/dataset/lib/DatasetIdAliases";
import type {
  DatasetCatalogResponse,
  DatasetDetail,
} from "@/shared/types/DatasetTypes";

interface DatasetCatalogRequestOptions {
  signal?: AbortSignal;
  force?: boolean;
}

interface DatasetDetailRequestOptions {
  signal?: AbortSignal;
  force?: boolean;
}

export interface DatasetServiceError extends Error {
  code?: number;
}

const createDatasetServiceError = (
  message: string,
  code?: number,
): DatasetServiceError => {
  const error = new Error(message) as DatasetServiceError;
  error.code = code;
  return error;
};

const DATASET_CATALOG_CACHE_KEY = "datasets:catalog";
const DATASET_DETAIL_CACHE_PREFIX = "datasets:detail";

const datasetDetailCacheKey = (datasetId: string): string =>
  `${DATASET_DETAIL_CACHE_PREFIX}:${normalizeDatasetId(datasetId)}`;

const loadCatalogFromApi = async (
  signal?: AbortSignal,
): Promise<DatasetCatalogResponse> => {
  const response = await request.get<unknown>("/datasets/catalog", {
    signal,
  });

  if (!response.success || !response.data) {
    throw createDatasetServiceError(
      response.message || "目录加载失败，请稍后重试。",
      response.code,
    );
  }

  return adaptDatasetCatalog(response.data as never);
};

const loadDetailFromApi = async (
  datasetId: string,
  signal?: AbortSignal,
): Promise<DatasetDetail> => {
  const response = await request.get<unknown>(`/datasets/${datasetId}`, {
    signal,
  });

  if (!response.success || !response.data) {
    throw createDatasetServiceError(
      response.message || "详情加载失败，请稍后重试。",
      response.code,
    );
  }

  return adaptDatasetDetail(response.data as never);
};

export const getDatasetCatalog = async (
  options: DatasetCatalogRequestOptions = {},
): Promise<DatasetCatalogResponse> => {
  const { force = false, signal } = options;

  if (ApiConfig.enableApiMock) {
    if (shouldMockFail("mockCatalogError")) {
      const result = await resolveMockEnvelope(
        createErrorEnvelope(50000, "目录加载失败，请稍后重试。", {
          catalogVersion: "",
          categoryCount: 0,
          subcategoryCount: 0,
          categories: [],
        }),
      );
      throw createDatasetServiceError(result.message, result.code);
    }

    const result = await resolveMockEnvelope(
      createSuccessEnvelope(buildReferenceDatasetCatalog()),
    );
    return adaptDatasetCatalog(result.data);
  }

  if (signal) {
    const cached = !force
      ? readMemoryCache<DatasetCatalogResponse>(DATASET_CATALOG_CACHE_KEY)
      : undefined;

    if (cached) {
      return cached;
    }

    const catalog = await loadCatalogFromApi(signal);
    return setMemoryCache(DATASET_CATALOG_CACHE_KEY, catalog);
  }

  return withMemoryCache(
    DATASET_CATALOG_CACHE_KEY,
    () => loadCatalogFromApi(signal),
    { force },
  );
};

export const getDatasetDetail = async (
  datasetId: string,
  options: DatasetDetailRequestOptions = {},
): Promise<DatasetDetail> => {
  const normalizedDatasetId = normalizeDatasetId(datasetId);
  const { force = false, signal } = options;
  const cacheKey = datasetDetailCacheKey(normalizedDatasetId);

  if (ApiConfig.enableApiMock) {
    if (shouldMockFail("mockDetailError")) {
      const result = await resolveMockEnvelope(
        createErrorEnvelope(50000, "详情加载失败，请稍后重试。", null),
      );
      throw createDatasetServiceError(result.message, result.code);
    }

    const detail = getReferenceDatasetDetail(normalizedDatasetId);
    if (!detail) {
      const result = await resolveMockEnvelope(
        createErrorEnvelope(40400, "未找到对应评测项。", null),
      );
      throw createDatasetServiceError(result.message, result.code);
    }

    const result = await resolveMockEnvelope(createSuccessEnvelope(detail));
    return adaptDatasetDetail(result.data);
  }

  if (signal) {
    const cached = !force
      ? readMemoryCache<DatasetDetail>(cacheKey)
      : undefined;

    if (cached) {
      return cached;
    }

    const detail = await loadDetailFromApi(normalizedDatasetId, signal);
    return setMemoryCache(cacheKey, detail);
  }

  return withMemoryCache(
    cacheKey,
    () => loadDetailFromApi(normalizedDatasetId, signal),
    { force },
  );
};
