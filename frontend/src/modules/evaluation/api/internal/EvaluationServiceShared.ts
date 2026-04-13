import type {
  EvaluationControls,
  EvaluationDetail,
  EvaluationFinalizationReason,
  EvaluationProgress,
  EvaluationRecord,
  EvaluationReport,
  EvaluationStatus,
  SubmitAgentPayload,
  SubmitMetaResponse,
} from "@/shared/types/AgentTypes";

export interface StoredEvaluationRecord {
  evaluationId: string;
  requestId: string;
  agentName: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  status: EvaluationStatus;
  publicToLeaderboard: boolean;
  datasetIds: string[];
  datasetNames: string[];
  submitMethod: "api" | "docker";
  score: number | null;
  ownerName: string;
  parameters: SubmitAgentPayload["parameters"];
  completedDatasetCount: number;
  pauseUsed: boolean;
  pauseDeadlineAt: string | null;
  finalReportAvailable: boolean;
  finalizationReason: EvaluationFinalizationReason | null;
  reportGeneratedAt: string | null;
  phaseStartedAt: string;
}

export interface ResolvedEvaluationState {
  evaluationId: string;
  agentName: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  status: EvaluationStatus;
  publicToLeaderboard: boolean;
  datasetIds: string[];
  datasetNames: string[];
  submitMethod: "api" | "docker";
  score: number | null;
  ownerName: string;
  parameters: SubmitAgentPayload["parameters"];
  progressPercent: number;
  finalReportAvailable: boolean;
  finalizationReason: EvaluationFinalizationReason | null;
  progress: EvaluationProgress;
  controls: EvaluationControls;
  report: EvaluationReport | null;
}

export interface ServiceError extends Error {
  code?: number;
}

export const MOCK_PENDING_DELAY_MS = 2200;
export const MOCK_DATASET_DURATION_MS = 3600;
export const MOCK_CANCEL_DELAY_MS = 800;
export const PAUSE_TIMEOUT_MS = 60 * 60 * 1000;
export const SUBMIT_META_CACHE_KEY = "agents:submit-meta";

export const nowIso = (): string => new Date().toISOString();
export const toTimestamp = (value: string): number => new Date(value).getTime();
export const toIso = (value: number): string => new Date(value).toISOString();

export const createServiceError = (
  message: string,
  code?: number,
): ServiceError => {
  const error = new Error(message) as ServiceError;
  error.code = code;
  return error;
};

const createSubmitMetaError = (): Error =>
  new Error("submit-meta 响应结构不符合新协议，请确认后端仅返回扁平结果。");

export const ensureSubmitMeta = (payload: unknown): SubmitMetaResponse => {
  if (!payload || typeof payload !== "object") {
    throw createSubmitMetaError();
  }

  const candidate = payload as Partial<SubmitMetaResponse>;

  if (
    !Array.isArray(candidate.supportedMethods) ||
    !candidate.difficulty ||
    !candidate.timeoutMinutes ||
    !candidate.retryEnabled ||
    !candidate.publicToLeaderboard
  ) {
    throw createSubmitMetaError();
  }

  return {
    supportedMethods: candidate.supportedMethods,
    difficulty: candidate.difficulty,
    timeoutMinutes: {
      ...candidate.timeoutMinutes,
      recommendedMax: candidate.timeoutMinutes.recommendedMax ?? 20,
    },
    retryEnabled: candidate.retryEnabled,
    publicToLeaderboard: candidate.publicToLeaderboard,
  };
};

export const getDatasetCount = (record: { datasetIds: string[] }): number =>
  Math.max(record.datasetIds.length, 1);

export const clampPercent = (value: number): number =>
  Math.min(100, Math.max(0, Math.round(value)));

export const computeScore = (
  record: {
    agentName: string;
    evaluationId: string;
    datasetIds: string[];
    parameters: SubmitAgentPayload["parameters"];
    submitMethod: "api" | "docker";
  },
  completedDatasetCount = record.datasetIds.length,
): number => {
  const completionRatio = completedDatasetCount / getDatasetCount(record);
  const datasetFactor = record.datasetIds.length * 1.8;
  const retryPenalty = record.parameters.retryEnabled ? 1.5 : 0;
  const difficultyBonus = record.parameters.difficulty * 7;
  const timeoutBonus = Math.min(record.parameters.timeoutMinutes, 24) * 0.18;
  const seed = record.agentName.length + record.evaluationId.length;
  const completionPenalty = (1 - completionRatio) * 10;
  const score =
    82 +
    datasetFactor +
    difficultyBonus +
    timeoutBonus -
    retryPenalty -
    completionPenalty +
    (seed % 4);

  return Number(Math.min(98.8, Math.max(70.6, score)).toFixed(1));
};

export const toEvaluationRecord = (
  state: ResolvedEvaluationState,
): EvaluationRecord => ({
  evaluationId: state.evaluationId,
  agentName: state.agentName,
  description: state.description,
  createdAt: state.createdAt,
  updatedAt: state.updatedAt,
  status: state.status,
  progressPercent: state.progressPercent,
  finalReportAvailable: state.finalReportAvailable,
  finalizationReason: state.finalizationReason,
  publicToLeaderboard: state.publicToLeaderboard,
  datasetIds: state.datasetIds,
  datasetNames: state.datasetNames,
  submitMethod: state.submitMethod,
  score: state.score,
  ownerName: state.ownerName,
  parameters: state.parameters,
});

export const toEvaluationDetail = (
  state: ResolvedEvaluationState,
): EvaluationDetail => ({
  ...toEvaluationRecord(state),
  progress: state.progress,
  controls: state.controls,
  report: state.report,
});
