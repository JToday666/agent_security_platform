export type SubmitMethod = "api" | "docker";
export type EvaluationStatus =
  | "pending"
  | "running"
  | "pausing"
  | "paused"
  | "terminating"
  | "canceling"
  | "completed"
  | "terminated"
  | "canceled"
  | "failed";

export type EvaluationFinalizationReason =
  | "completed"
  | "terminated_by_user"
  | "auto_terminated_after_pause_timeout"
  | "canceled_by_user"
  | "failed";

export type EvaluationAction = "pause" | "resume" | "terminate" | "cancel";

export interface SubmitParameters {
  difficulty: number;
  timeoutMinutes: number;
  retryEnabled: boolean;
}

export interface SubmitApiPayload {
  baseUrl: string;
  token?: string;
}

export interface SubmitDockerPayload {
  imageUri: string;
  username?: string;
  password?: string;
}

export interface SubmitAgentPayload {
  agentName: string;
  description?: string;
  submitMethod: SubmitMethod;
  api?: SubmitApiPayload | null;
  docker?: SubmitDockerPayload | null;
  parameters: SubmitParameters;
  publicToLeaderboard: boolean;
  selectedDatasetIds: string[];
  requestId: string;
}

export interface SubmitAgentApiPayload extends Omit<
  SubmitAgentPayload,
  "selectedDatasetIds"
> {
  datasetIds: string[];
}

export interface RangeMeta {
  min: number;
  max: number;
  step: number;
  default: number;
  recommendedMax?: number;
}

export interface BooleanMeta {
  default: boolean;
}

export interface SubmitMetaResponse {
  supportedMethods: SubmitMethod[];
  difficulty: RangeMeta;
  timeoutMinutes: RangeMeta;
  retryEnabled: BooleanMeta;
  publicToLeaderboard: BooleanMeta;
}

export interface PrecheckResponse {
  ok: boolean;
  warnings: string[];
}

export interface SubmitResponse {
  evaluationId: string;
  status: EvaluationStatus;
  createdAt: string;
}

export interface PendingSubmitRequest {
  requestId: string;
  payloadDigest: string;
  createdAt: string;
}

export interface SubmitFieldErrors {
  agentName?: string;
  apiBaseUrl?: string;
  dockerImageUri?: string;
  selectedDatasetIds?: string;
  requestId?: string;
}

export interface EvaluationRecord {
  evaluationId: string;
  agentName: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  status: EvaluationStatus;
  progressPercent: number;
  finalReportAvailable: boolean;
  finalizationReason: EvaluationFinalizationReason | null;
  publicToLeaderboard: boolean;
  datasetIds: string[];
  datasetNames: string[];
  submitMethod: SubmitMethod;
  score: number | null;
  ownerName: string;
  parameters: SubmitParameters;
}

export interface EvaluationMetric {
  name: string;
  value: string;
  percentage: number;
  description: string;
}

export interface EvaluationReportRiskCategoryItem {
  categoryId: string;
  name: string;
  totalSamples: number;
  taskCompletedCount: number;
  harmDetectedCount: number;
}

export interface EvaluationReportLevelItem {
  level: number;
  totalSamples: number;
  harmDetectedCount: number;
}

export interface EvaluationProgress {
  percent: number;
  totalDatasetCount: number;
  completedDatasetCount: number;
  runningDatasetId: string | null;
  runningDatasetName: string | null;
  pauseDeadlineAt: string | null;
  statusText: string;
}

export interface EvaluationControls {
  canPause: boolean;
  canResume: boolean;
  canTerminate: boolean;
  canCancel: boolean;
  pauseUsed: boolean;
}

export interface EvaluationReport {
  reportStatus: string;
  summary: {
    totalSamples: number;
    completedSamples: number;
    taskCompletedCount: number;
    harmDetectedCount: number;
    failedCount: number;
    byRiskCategory: EvaluationReportRiskCategoryItem[];
    byRiskLevel: EvaluationReportLevelItem[];
    byAttackLevel: EvaluationReportLevelItem[];
  };
  reportUri: string | null;
  generatedAt: string;
  warnings: string[];
  metrics: EvaluationMetric[];
}

export interface EvaluationDetail extends Omit<
  EvaluationRecord,
  "progressPercent"
> {
  progress: EvaluationProgress;
  controls: EvaluationControls;
  report: EvaluationReport | null;
}

export interface EvaluationActionRequest {
  action: EvaluationAction;
}

export interface SubmitFormState {
  submitMethod: SubmitMethod;
  agentName: string;
  description: string;
  api: {
    baseUrl: string;
    token: string;
  };
  docker: {
    imageUri: string;
    username: string;
    password: string;
  };
  parameters: SubmitParameters;
  publicToLeaderboard: boolean;
  selectedDatasetIds: string[];
}
