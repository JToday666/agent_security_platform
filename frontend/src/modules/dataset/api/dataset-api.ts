import request from "@/shared/api/http-client";
import { ApiConfig } from "@/shared/api/Config";
import { getCurrentDisplayLocale } from "@/app/i18n";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import {
  readMemoryCache,
  setMemoryCache,
  withMemoryCache,
} from "@/shared/api/memory-cache";
import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
  shouldMockFail,
} from "@/shared/api/mock-api-utils";
import {
  adaptDatasetCatalog,
  adaptDatasetDetail,
} from "@/modules/dataset/api/adapters/dataset-adapters";
import {
  buildReferenceDatasetCatalog,
  getReferenceDatasetDetail,
} from "@/modules/dataset/mock/dataset-fixtures";
import { normalizeDatasetId } from "@/modules/dataset/model/dataset-id-aliases";
import type {
  DatasetCatalogResponse,
  DatasetDetail,
} from "@/shared/types/dataset-types";

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

const localizedCacheKey = (key: string): string =>
  `${key}:${getCurrentDisplayLocale()}`;

const datasetDetailCacheKey = (datasetId: string): string =>
  localizedCacheKey(
    `${DATASET_DETAIL_CACHE_PREFIX}:${normalizeDatasetId(datasetId)}`,
  );

const loadCatalogFromApi = async (
  signal?: AbortSignal,
): Promise<DatasetCatalogResponse> => {
  const response = await request.get<unknown>("/datasets/catalog", {
    signal,
  });

  if (!response.success || !response.data) {
    throw createDatasetServiceError(
      response.message || translateRuntimeMessage("dataset.api.catalogLoadFailed"),
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
      response.message || translateRuntimeMessage("dataset.api.detailLoadFailed"),
      response.code,
    );
  }

  return adaptDatasetDetail(response.data as never);
};

export const getDatasetCatalog = async (
  options: DatasetCatalogRequestOptions = {},
): Promise<DatasetCatalogResponse> => {
  const { force = false, signal } = options;
  const catalogCacheKey = localizedCacheKey(DATASET_CATALOG_CACHE_KEY);

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
      ? readMemoryCache<DatasetCatalogResponse>(catalogCacheKey)
      : undefined;

    if (cached) {
      return cached;
    }

    const catalog = await loadCatalogFromApi(signal);
    return setMemoryCache(catalogCacheKey, catalog);
  }

  return withMemoryCache(
    catalogCacheKey,
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
