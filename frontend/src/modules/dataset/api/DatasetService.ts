import request from "@/shared/api/core/HttpClient";
import { ApiConfig } from "@/shared/api/core/Config";
import {
  withMemoryCache,
  readMemoryCache,
  setMemoryCache,
} from "@/shared/api/core/MemoryCache";
import {
  adaptDatasetCatalog,
  adaptDatasetDetail,
} from "@/modules/dataset/api/adapters/DatasetAdapters";
import type {
  DatasetCatalogResponse,
  DatasetDetail,
} from "@/shared/types/DatasetTypes";
import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
  shouldMockFail,
} from "@/shared/api/core/MockApiUtils";
import {
  buildReferenceDatasetCatalog,
  getReferenceDatasetDetail,
} from "@/modules/dataset/mock/DatasetFixtures";
import { normalizeDatasetId } from "@/modules/dataset/lib/DatasetIdAliases";

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
const useLiveReferenceApi = !ApiConfig.enableApiMock;

const datasetDetailCacheKey = (datasetId: string): string =>
  `${DATASET_DETAIL_CACHE_PREFIX}:${normalizeDatasetId(datasetId)}`;

export const getDatasetCatalog = async (
  options: DatasetCatalogRequestOptions = {},
): Promise<DatasetCatalogResponse> => {
  const { force = false, signal } = options;
  const loadCatalog = async (): Promise<DatasetCatalogResponse> => {
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

    const catalog = await loadCatalog();
    return setMemoryCache(DATASET_CATALOG_CACHE_KEY, catalog);
  }

  return withMemoryCache(DATASET_CATALOG_CACHE_KEY, loadCatalog, { force });

  if (useLiveReferenceApi) {
    const response = await request.get<DatasetCatalogResponse>(
      "/datasets/catalog",
      {
        signal,
      },
    );

    if (!response.success || !response.data) {
      throw createDatasetServiceError(
        response.message || "目录加载失败。",
        response.code,
      );
    }

    return response.data as DatasetCatalogResponse;
  }

  if (shouldMockFail("mockCatalogError")) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(50000, "目录加载失败，请稍后重试。", {
        catalogVersion: "",
        categoryCount: 0,
        subcategoryCount: 0,
        categories: [],
      }),
    );
    throw new Error(result.message);
  }

  const result = await resolveMockEnvelope(
    createSuccessEnvelope(buildReferenceDatasetCatalog()),
  );

  return result.data as DatasetCatalogResponse;
};

export const getDatasetDetail = async (
  datasetId: string,
  options: DatasetDetailRequestOptions = {},
): Promise<DatasetDetail> => {
  const normalizedDatasetId = normalizeDatasetId(datasetId);
  const { force = false, signal } = options;
  const cacheKey = datasetDetailCacheKey(normalizedDatasetId);
  const loadDetail = async (): Promise<DatasetDetail> => {
    const response = await request.get<unknown>(
      `/datasets/${normalizedDatasetId}`,
      {
        signal,
      },
    );

    if (!response.success || !response.data) {
      throw createDatasetServiceError(
        response.message || "详情加载失败，请稍后重试。",
        response.code,
      );
    }

    return adaptDatasetDetail(response.data as never);
  };

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

    const detail = await loadDetail();
    return setMemoryCache(cacheKey, detail);
  }

  return withMemoryCache(cacheKey, loadDetail, { force });

  if (useLiveReferenceApi) {
    const response = await request.get<DatasetDetail>(
      `/datasets/${datasetId}`,
      {
        signal: options.signal,
      },
    );

    if (!response.success || !response.data) {
      throw createDatasetServiceError(
        response.message || "详情加载失败，请重试。",
        response.code,
      );
    }

    return response.data as DatasetDetail;
  }

  if (shouldMockFail("mockDetailError")) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(50000, "详情加载失败，请重试。", null),
    );
    throw createDatasetServiceError(result.message, result.code);
  }

  const detail = getReferenceDatasetDetail(datasetId) as DatasetDetail | null;
  if (!detail) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40400, "评测项不存在。", null),
    );
    throw createDatasetServiceError(result.message, result.code);
  }

  const result = await resolveMockEnvelope(createSuccessEnvelope(detail));
  return result.data as DatasetDetail;
};
