import request from "@/utils/request";
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
  referenceSubmitMeta,
} from "@/api/fixtures/ReferenceData";
import { isStepAligned } from "@/utils/SubmitParameterUtils";

interface DatasetCatalogRequestOptions {
  difficulty?: number;
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

const useLiveReferenceApi =
  import.meta.env.VITE_USE_LIVE_REFERENCE_API === "true";

const validateDifficulty = (difficulty?: number) => {
  if (typeof difficulty !== "number") {
    return;
  }

  const meta = referenceSubmitMeta.difficulty;
  const outOfRange = difficulty < meta.min || difficulty > meta.max;

  if (outOfRange || !isStepAligned(difficulty, meta)) {
    throw new Error("参数超出允许范围。");
  }
};

export const getDatasetCatalog = async (
  options: DatasetCatalogRequestOptions = {},
): Promise<DatasetCatalogResponse> => {
  const { difficulty, signal } = options;
  validateDifficulty(difficulty);

  if (useLiveReferenceApi) {
    const response = await request.get<DatasetCatalogResponse>(
      "/datasets/catalog",
      {
        params:
          typeof difficulty === "number"
            ? { difficulty: difficulty.toFixed(1) }
            : undefined,
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
    createSuccessEnvelope(buildReferenceDatasetCatalog(difficulty)),
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
      createErrorEnvelope(40400, "数据集不存在。", null),
    );
    throw createDatasetServiceError(result.message, result.code);
  }

  const result = await resolveMockEnvelope(createSuccessEnvelope(detail));
  return result.data;
};
