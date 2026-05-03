import request from "@/shared/api/http-client";
import { withMemoryCache } from "@/shared/api/memory-cache";
import {
  adaptEvaluationDetail,
  adaptEvaluationRecord,
  adaptSubmitMeta,
} from "@/modules/evaluation/api/adapters/agent-adapters";
import {
  adaptEvaluationReportPayload as adaptReportPayload,
  adaptEvaluationScoreTrend as adaptScoreTrend,
} from "@/modules/evaluation/api/adapters/report-adapters";
import type {
  EvaluationScoreTrendScope,
  EvaluationAction,
  EvaluationActionRequest,
  EvaluationDetail,
  EvaluationReportPayload,
  EvaluationRecord,
  EvaluationScoreTrend,
  PrecheckResponse,
  SubmitAgentPayload,
  SubmitMetaResponse,
  SubmitResponse,
} from "@/shared/types/agent-types";
import { buildEvaluationCreatePayload } from "@/modules/submission/model/parameter-validator";
import {
  createServiceError,
  SUBMIT_META_CACHE_KEY,
} from "./evaluation-service-shared";
import {
  sanitizeEvaluationDetail,
  sanitizeEvaluationRecord,
} from "./evaluation-service-view";

export const getLiveSubmitMeta = async (): Promise<SubmitMetaResponse> =>
  withMemoryCache(
    SUBMIT_META_CACHE_KEY,
    async () => {
      const response = await request.get<unknown>("/evaluations/meta");

      if (!response.success || !response.data) {
        throw createServiceError(
          response.message || "提交元数据加载失败。",
          response.code,
        );
      }

      return adaptSubmitMeta(response.data as never);
    },
    { force: false },
  );

export const precheckLiveAgent = async (
  payload: SubmitAgentPayload,
): Promise<PrecheckResponse> => {
  const response = await request.post<{
    ok: boolean;
    warnings?: Array<string | { message?: string }>;
  }>(
    "/evaluations/validate",
    buildEvaluationCreatePayload(payload),
  );

  if (!response.success || !response.data) {
    throw createServiceError(response.message || "预检查失败。", response.code);
  }

  return {
    ok: Boolean(response.data.ok),
    warnings: Array.isArray(response.data.warnings)
      ? response.data.warnings
          .map((item) =>
            typeof item === "string" ? item : item.message?.trim() ?? "",
          )
          .filter((item) => item.length > 0)
      : [],
  };
};

export const submitLiveAgent = async (
  payload: SubmitAgentPayload,
): Promise<SubmitResponse> => {
  const response = await request.post<SubmitResponse>(
    "/evaluations",
    buildEvaluationCreatePayload(payload),
  );

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message || "提交失败，请稍后重试。",
      response.code,
    );
  }

  return response.data;
};

export const getLiveEvaluationRecords = async (): Promise<
  EvaluationRecord[]
> => {
  const response = await request.get<unknown>("/evaluations");

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message || "评测记录加载失败。",
      response.code,
    );
  }

  const payload =
    response.data &&
    typeof response.data === "object" &&
    Array.isArray((response.data as { items?: unknown }).items)
      ? (response.data as { items: unknown[] }).items
      : Array.isArray(response.data)
        ? response.data
        : [];

  return payload.map((item) =>
    sanitizeEvaluationRecord(adaptEvaluationRecord(item)),
  );
};

export const getLiveEvaluationScoreTrend = async (
  scope: EvaluationScoreTrendScope,
): Promise<EvaluationScoreTrend> => {
  const response = await request.get<unknown>("/evaluations/score-trend", {
    params: { scope },
  });

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message || "评测趋势加载失败。",
      response.code,
    );
  }

  return adaptScoreTrend(response.data);
};

export const getLiveEvaluationDetail = async (
  evaluationId: string,
): Promise<EvaluationDetail> => {
  const response = await request.get<EvaluationDetail>(
    `/evaluations/${evaluationId}`,
  );

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message || "评测详情加载失败。",
      response.code,
    );
  }

  return sanitizeEvaluationDetail(adaptEvaluationDetail(response.data));
};

export const getLiveEvaluationReport = async (
  evaluationId: string,
): Promise<EvaluationReportPayload> => {
  const response = await request.get<unknown>(`/evaluations/${evaluationId}/report`);

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message || "评测报告加载失败。",
      response.code,
    );
  }

  return adaptReportPayload(response.data);
};

export const downloadLiveEvaluationSampleDetails = async (
  evaluationId: string,
) => request.download(`/evaluations/${evaluationId}/samples/export`);

export const postLiveEvaluationAction = async (
  evaluationId: string,
  action: EvaluationAction,
): Promise<EvaluationDetail> => {
  const response = await request.post<EvaluationDetail>(
    `/evaluations/${evaluationId}/actions`,
    { action } as EvaluationActionRequest,
  );

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message || "任务操作失败。",
      response.code,
    );
  }

  return sanitizeEvaluationDetail(adaptEvaluationDetail(response.data));
};
