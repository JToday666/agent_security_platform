import request from "@/shared/api/http-client";
import { withMemoryCache } from "@/shared/api/memory-cache";
import { getCurrentDisplayLocale } from "@/app/i18n";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import {
  adaptEvaluationDetail,
  adaptEvaluationRecord,
  adaptSubmitMeta,
} from "@/modules/evaluation/api/adapters/agent-adapters";
import {
  adaptEvaluationReportPayload as adaptReportPayload,
} from "@/modules/evaluation/api/adapters/report-adapters";
import type {
  EvaluationAction,
  EvaluationActionRequest,
  EvaluationDetail,
  EvaluationReportPayload,
  EvaluationRecord,
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
    `${SUBMIT_META_CACHE_KEY}:${getCurrentDisplayLocale()}`,
    async () => {
      const response = await request.get<unknown>("/evaluations/meta");

      if (!response.success || !response.data) {
        throw createServiceError(
          response.message ||
            translateRuntimeMessage("evaluation.api.submitMetaLoadFailed"),
          response.code,
        );
      }

      return adaptSubmitMeta(response.data);
    },
    { force: false },
  );

export const precheckLiveAgent = async (
  payload: SubmitAgentPayload,
): Promise<PrecheckResponse> => {
  const response = await request.post<{
    ok: boolean;
    warnings?: Array<string | { message?: string }>;
  }>("/evaluations/validate", buildEvaluationCreatePayload(payload));

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message ||
        translateRuntimeMessage("evaluation.api.submitPrecheckFailed"),
      response.code,
    );
  }

  return {
    ok: Boolean(response.data.ok),
    warnings: Array.isArray(response.data.warnings)
      ? response.data.warnings
          .map((item) =>
            typeof item === "string" ? item : (item.message?.trim() ?? ""),
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
      response.message ||
        translateRuntimeMessage("evaluation.api.submitFailed"),
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
      response.message ||
        translateRuntimeMessage("evaluation.api.recordsLoadFailed"),
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

export const getLiveEvaluationDetail = async (
  evaluationId: string,
): Promise<EvaluationDetail> => {
  const response = await request.get<EvaluationDetail>(
    `/evaluations/${evaluationId}`,
  );

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message ||
        translateRuntimeMessage("evaluation.api.detailLoadFailed"),
      response.code,
    );
  }

  return sanitizeEvaluationDetail(adaptEvaluationDetail(response.data));
};

export const getLiveEvaluationReport = async (
  evaluationId: string,
): Promise<EvaluationReportPayload> => {
  const response = await request.get<unknown>(
    `/evaluations/${evaluationId}/report`,
  );

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message ||
        translateRuntimeMessage("evaluation.api.reportLoadFailed"),
      response.code,
    );
  }

  return adaptReportPayload(response.data);
};

export const downloadLiveEvaluationSampleDetails = async (
  sampleDetailsUrl: string,
) => request.download(sampleDetailsUrl);

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
      response.message ||
        translateRuntimeMessage("evaluation.api.actionFailed"),
      response.code,
    );
  }

  return sanitizeEvaluationDetail(adaptEvaluationDetail(response.data));
};
