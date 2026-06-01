import type {
  EvaluationControls,
  EvaluationDetail,
  EvaluationFinalizationReason,
  EvaluationDownloads,
  EvaluationProgress,
  EvaluationRecord,
  EvaluationReport,
  EvaluationRepresentativeSamples,
  EvaluationSampleSummary,
  EvaluationStatus,
  SubmitAgentPayload,
} from "@/shared/types/agent-types";

export interface ResolvedEvaluationState {
  evaluationId: string;
  agentName: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  startedAt?: string | null;
  finishedAt?: string | null;
  status: EvaluationStatus;
  publicToLeaderboard: boolean;
  leaderboardDisplayMode: "public" | "anonymous";
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
  sampleSummary?: EvaluationSampleSummary | null;
  representativeSamples?: EvaluationRepresentativeSamples;
  downloads?: EvaluationDownloads;
}

export interface ServiceError extends Error {
  code?: number;
}

export const SUBMIT_META_CACHE_KEY = "agents:submit-meta";

export const createServiceError = (
  message: string,
  code?: number,
): ServiceError => {
  const error = new Error(message) as ServiceError;
  error.code = code;
  return error;
};

export const clampPercent = (value: number): number =>
  Math.min(100, Math.max(0, Math.round(value)));

export const toEvaluationRecord = (
  state: ResolvedEvaluationState,
): EvaluationRecord => ({
  evaluationId: state.evaluationId,
  agentName: state.agentName,
  description: state.description,
  createdAt: state.createdAt,
  updatedAt: state.updatedAt,
  finishedAt: state.finishedAt ?? null,
  status: state.status,
  progressPercent: state.progressPercent,
  finalReportAvailable: state.finalReportAvailable,
  finalizationReason: state.finalizationReason,
  publicToLeaderboard: state.publicToLeaderboard,
  leaderboardDisplayMode: state.leaderboardDisplayMode,
  datasetIds: state.datasetIds,
  datasetNames: state.datasetNames,
  submitMethod: state.submitMethod,
  score: state.score,
  ownerName: state.ownerName,
  parameters: state.parameters,
  sampleSummary: state.sampleSummary ?? null,
});

export const toEvaluationDetail = (
  state: ResolvedEvaluationState,
): EvaluationDetail => ({
  ...toEvaluationRecord(state),
  startedAt: state.startedAt ?? null,
  finishedAt: state.finishedAt ?? null,
  progress: state.progress,
  controls: state.controls,
  report: state.report,
  sampleSummary: state.sampleSummary ?? null,
  representativeSamples: state.representativeSamples ?? {
    success: null,
    failed: null,
    error: null,
  },
  downloads: state.downloads ?? {
    sampleDetailsUrl: null,
  },
});
