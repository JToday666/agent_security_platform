import { ApiConfig } from "@/shared/api/Config";
import type {
  EvaluationAction,
  EvaluationDetail,
  EvaluationRecord,
  PrecheckResponse,
  SubmitAgentPayload,
  SubmitMetaResponse,
  SubmitResponse,
} from "@/shared/types/agent-types";
import {
  getLiveEvaluationDetail,
  getLiveEvaluationRecords,
  getLiveSubmitMeta,
  postLiveEvaluationAction,
  precheckLiveAgent,
  submitLiveAgent,
} from "./internal/live-evaluation-api";
import {
  getMockEvaluationDetail,
  getMockEvaluationRecords,
  getMockSubmitMeta,
  postMockEvaluationAction,
  precheckMockAgent,
  submitMockAgent,
} from "./internal/mock-evaluation-api";

const useMockApi = ApiConfig.enableApiMock;

export const getSubmitMeta = async (): Promise<SubmitMetaResponse> =>
  useMockApi ? getMockSubmitMeta() : getLiveSubmitMeta();

export const precheckAgent = async (
  payload: SubmitAgentPayload,
): Promise<PrecheckResponse> =>
  useMockApi ? precheckMockAgent(payload) : precheckLiveAgent(payload);

export const submitAgent = async (
  payload: SubmitAgentPayload,
): Promise<SubmitResponse> =>
  useMockApi ? submitMockAgent(payload) : submitLiveAgent(payload);

export const getEvaluationRecords = async (): Promise<EvaluationRecord[]> =>
  useMockApi ? getMockEvaluationRecords() : getLiveEvaluationRecords();

export const getEvaluationDetail = async (
  evaluationId: string,
): Promise<EvaluationDetail> =>
  useMockApi
    ? getMockEvaluationDetail(evaluationId)
    : getLiveEvaluationDetail(evaluationId);

export const postEvaluationAction = async (
  evaluationId: string,
  action: EvaluationAction,
): Promise<EvaluationDetail> =>
  useMockApi
    ? postMockEvaluationAction(evaluationId, action)
    : postLiveEvaluationAction(evaluationId, action);
