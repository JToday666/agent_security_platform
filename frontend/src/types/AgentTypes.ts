export type SubmitMethod = "api" | "docker";

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

export interface LegacySubmitMetaResponse {
  supportedMethods: SubmitMethod[];
  parameterMeta: {
    difficulty: RangeMeta;
    timeoutMinutes: RangeMeta;
    retryEnabled: BooleanMeta;
    publicToLeaderboard: BooleanMeta;
  };
}

export type SubmitMetaApiResponse =
  | SubmitMetaResponse
  | LegacySubmitMetaResponse;

export interface PrecheckResponse {
  ok: boolean;
  warnings: string[];
}

export interface SubmitResponse {
  evaluationId: string;
  status: "pending" | "running" | "completed";
  createdAt: string;
}

export interface EvaluationRecord {
  evaluationId: string;
  agentName: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  status: "pending" | "running" | "completed";
  publicToLeaderboard: boolean;
  datasetIds: string[];
  datasetNames: string[];
  submitMethod: SubmitMethod;
  score?: number;
  ownerName: string;
  parameters: SubmitParameters;
}

export interface EvaluationMetric {
  name: string;
  value: string;
  percentage: number;
  description: string;
}

export interface EvaluationDetail extends EvaluationRecord {
  summary: string;
  warnings: string[];
  metrics: EvaluationMetric[];
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

export interface SubmitFormPersistedData {
  submitMethod: SubmitMethod;
  agentName: string;
  description: string;
  api: {
    baseUrl: string;
  };
  docker: {
    imageUri: string;
    username: string;
  };
  parameters: SubmitParameters;
  publicToLeaderboard: boolean;
  selectedDatasetIds: string[];
  expandedCategoryIds: string[];
}
