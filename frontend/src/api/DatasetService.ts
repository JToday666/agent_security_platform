import request from "@/utils/request";
import { ApiConfig } from "@/api/Config";
import type {
  DatasetCatalogResponse,
  DatasetDetail,
} from "@/types/DatasetTypes";
import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
  shouldMockFail,
} from "@/api/MockApiUtils";
import {
  buildReferenceDatasetCatalog,
  getReferenceDatasetDetail,
} from "@/api/fixtures/DatasetFixtures";

interface DatasetCatalogRequestOptions {
  signal?: AbortSignal;
}

interface DatasetDetailRequestOptions {
  signal?: AbortSignal;
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

const useLiveReferenceApi = ApiConfig.reference.useLive;

export const getDatasetCatalog = async (
  options: DatasetCatalogRequestOptions = {},
): Promise<DatasetCatalogResponse> => {
  const { signal } = options;

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

    return response.data;
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

  return result.data;
};

export const getDatasetDetail = async (
  datasetId: string,
  options: DatasetDetailRequestOptions = {},
): Promise<DatasetDetail> => {
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

    return response.data;
  }

  if (shouldMockFail("mockDetailError")) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(50000, "详情加载失败，请重试。", null),
    );
    throw createDatasetServiceError(result.message, result.code);
  }

  const detail = getReferenceDatasetDetail(datasetId);
  if (!detail) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40400, "评测项不存在。", null),
    );
    throw createDatasetServiceError(result.message, result.code);
  }

  const result = await resolveMockEnvelope(createSuccessEnvelope(detail));
  return result.data;
};
