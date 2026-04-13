import request from "@/shared/api/HttpClient";
import { withMemoryCache } from "@/shared/api/MemoryCache";
import { buildSubmitAgentApiPayload } from "@/modules/dataset/api/adapters/DatasetAdapters";
import {
  adaptEvaluationDetail,
  adaptEvaluationRecord,
  adaptSubmitMeta,
} from "@/modules/evaluation/api/adapters/AgentAdapters";
import type {
  EvaluationAction,
  EvaluationActionRequest,
  EvaluationDetail,
  EvaluationRecord,
  PrecheckResponse,
  SubmitAgentPayload,
  SubmitMetaResponse,
  SubmitResponse,
} from "@/shared/types/AgentTypes";
import {
  createServiceError,
  SUBMIT_META_CACHE_KEY,
} from "./EvaluationServiceShared";
import {
  sanitizeEvaluationDetail,
  sanitizeEvaluationRecord,
} from "./EvaluationServiceView";

export const getLiveSubmitMeta = async (): Promise<SubmitMetaResponse> =>
  withMemoryCache(
    SUBMIT_META_CACHE_KEY,
    async () => {
      const response = await request.get<unknown>("/agents/submit-meta");

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
  const response = await request.post<PrecheckResponse>(
    "/agents/precheck",
    buildSubmitAgentApiPayload(payload),
  );

  if (!response.success || !response.data) {
    throw createServiceError(response.message || "预检查失败。", response.code);
  }

  return response.data;
};

export const submitLiveAgent = async (
  payload: SubmitAgentPayload,
): Promise<SubmitResponse> => {
  const response = await request.post<SubmitResponse>(
    "/agents/submit",
    buildSubmitAgentApiPayload(payload),
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
  const response = await request.get<EvaluationRecord[]>("/evaluations");

  if (!response.success || !response.data) {
    throw createServiceError(
      response.message || "评测记录加载失败。",
      response.code,
    );
  }

  return (response.data as unknown[]).map((item) =>
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
      response.message || "评测详情加载失败。",
      response.code,
    );
  }

  return sanitizeEvaluationDetail(adaptEvaluationDetail(response.data));
};

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
