import request from "@/shared/api/http-client";
import { getCurrentDisplayLocale } from "@/app/i18n";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import {
  readMemoryCache,
  setMemoryCache,
  withMemoryCache,
} from "@/shared/api/memory-cache";
import {
  adaptDatasetCatalog,
  adaptDatasetDetail,
} from "@/modules/dataset/api/adapters/dataset-adapters";
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
  localizedCacheKey(`${DATASET_DETAIL_CACHE_PREFIX}:${datasetId.trim()}`);

const loadCatalogFromApi = async (
  signal?: AbortSignal,
): Promise<DatasetCatalogResponse> => {
  const response = await request.get<unknown>("/datasets/catalog", {
    signal,
  });

  if (!response.success || !response.data) {
    throw createDatasetServiceError(
      response.message ||
        translateRuntimeMessage("dataset.api.catalogLoadFailed"),
      response.code,
    );
  }

  return adaptDatasetCatalog(response.data);
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
      response.message ||
        translateRuntimeMessage("dataset.api.detailLoadFailed"),
      response.code,
    );
  }

  return adaptDatasetDetail(response.data);
};

export const getDatasetCatalog = async (
  options: DatasetCatalogRequestOptions = {},
): Promise<DatasetCatalogResponse> => {
  const { force = false, signal } = options;
  const catalogCacheKey = localizedCacheKey(DATASET_CATALOG_CACHE_KEY);

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

  return withMemoryCache(catalogCacheKey, () => loadCatalogFromApi(signal), {
    force,
  });
};

export const getDatasetDetail = async (
  datasetId: string,
  options: DatasetDetailRequestOptions = {},
): Promise<DatasetDetail> => {
  const requestedDatasetId = datasetId.trim();
  const { force = false, signal } = options;
  const cacheKey = datasetDetailCacheKey(requestedDatasetId);

  if (signal) {
    const cached = !force
      ? readMemoryCache<DatasetDetail>(cacheKey)
      : undefined;

    if (cached) {
      return cached;
    }

    const detail = await loadDetailFromApi(requestedDatasetId, signal);
    return setMemoryCache(cacheKey, detail);
  }

  return withMemoryCache(
    cacheKey,
    () => loadDetailFromApi(requestedDatasetId, signal),
    { force },
  );
};
