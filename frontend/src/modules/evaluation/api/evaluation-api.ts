import { ApiConfig } from "@/shared/api/Config";
import type {
  EvaluationScoreTrendScope,
  EvaluationAction,
  EvaluationDetail,
  EvaluationReportPayload,
  EvaluationRecord,
  EvaluationScoreTrend,
  PrecheckResponse,
  SubmitAgentPayload,
  SubmitMetaResponse,
  SubmitResponse,
} from "@/shared/types/agent-types";
import type { ApiBlobResponse } from "@/shared/api/http-client";
import {
  downloadLiveEvaluationSampleDetails,
  getLiveEvaluationDetail,
  getLiveEvaluationReport,
  getLiveEvaluationRecords,
  getLiveEvaluationScoreTrend,
  getLiveSubmitMeta,
  postLiveEvaluationAction,
  precheckLiveAgent,
  submitLiveAgent,
} from "./internal/live-evaluation-api";
import {
  getMockEvaluationDetail,
  getMockEvaluationReport,
  getMockEvaluationRecords,
} from "./internal/mock-evaluation-api";

const useMockApi = ApiConfig.enableApiMock;

export const getSubmitMeta = async (): Promise<SubmitMetaResponse> =>
  getLiveSubmitMeta();

export const precheckAgent = async (
  payload: SubmitAgentPayload,
): Promise<PrecheckResponse> =>
  precheckLiveAgent(payload);

export const submitAgent = async (
  payload: SubmitAgentPayload,
): Promise<SubmitResponse> =>
  submitLiveAgent(payload);

export const getEvaluationRecords = async (): Promise<EvaluationRecord[]> =>
  useMockApi ? getMockEvaluationRecords() : getLiveEvaluationRecords();

export const getEvaluationScoreTrend = async (
  scope: EvaluationScoreTrendScope,
): Promise<EvaluationScoreTrend> =>
  getLiveEvaluationScoreTrend(scope);

export const getEvaluationDetail = async (
  evaluationId: string,
): Promise<EvaluationDetail> =>
  useMockApi
    ? getMockEvaluationDetail(evaluationId)
    : getLiveEvaluationDetail(evaluationId);

export const getEvaluationReport = async (
  evaluationId: string,
): Promise<EvaluationReportPayload> =>
  useMockApi
    ? getMockEvaluationReport(evaluationId)
    : getLiveEvaluationReport(evaluationId);

export const downloadEvaluationSampleDetails = async (
  evaluationId: string,
): Promise<ApiBlobResponse> =>
  downloadLiveEvaluationSampleDetails(evaluationId);

export const postEvaluationAction = async (
  evaluationId: string,
  action: EvaluationAction,
): Promise<EvaluationDetail> =>
  postLiveEvaluationAction(evaluationId, action);
