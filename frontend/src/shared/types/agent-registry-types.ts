export type AgentInvokeMode = "sync_response" | "submit_poll";

export type AgentStatus =
  | "draft"
  | "verifying"
  | "active"
  | "invalid"
  | "archived";

export type AgentTemplateLevel = "basic" | "advanced";

export type AgentAuthType =
  | "none"
  | "bearer"
  | "api_key_header"
  | "custom_header";

export type AgentTaskRenderMode = "goal_only";

export interface AgentConnectionConfig {
  baseUrl: string;
  invokePath: string;
  resultPathTemplate?: string;
  requestTimeoutSeconds: number;
  pollIntervalSeconds: number;
  pollTimeoutSeconds: number;
}

export interface AgentAuthCreateConfig {
  type: AgentAuthType;
  config: Record<string, string>;
}

export interface AgentAuthPublicSummary {
  type: AgentAuthType;
  hasCredential?: boolean;
  publicConfig?: Record<string, unknown>;
  config?: Record<string, string>;
}

export interface AgentStructuredOutputOption {
  supported: boolean;
  fieldAlias: string;
}

export interface AgentRequestOptions {
  structuredOutput: AgentStructuredOutputOption;
}

export interface AgentInputMapping {
  task: string;
  entryUrl?: string;
  timeoutSeconds?: string;
  sampleId?: string;
  evaluationId?: string;
  maxSteps?: string;
}

export interface AgentOutputMapping {
  externalRunId?: string;
  status?: string;
  finalAnswer?: string;
  errorMessage?: string;
  stepCount?: string;
  artifacts?: string;
}

export interface AgentDefaultConfig {
  invokeMode: AgentInvokeMode;
  connection: AgentConnectionConfig;
  auth: AgentAuthCreateConfig;
  platformInputMapping: AgentInputMapping;
  taskRenderMode: AgentTaskRenderMode;
  customRequestBody: Record<string, unknown>;
  requestOptions: AgentRequestOptions;
  platformOutputMapping: AgentOutputMapping;
  terminalStatuses: string[];
  successStatuses: string[];
}

export interface AgentTemplate {
  templateId: string;
  name: string;
  description: string;
  recommended: boolean;
  sortOrder: number;
  level: AgentTemplateLevel;
  tags: string[];
  defaultConfig: AgentDefaultConfig;
}

export interface AgentCreatePayload extends AgentDefaultConfig {
  templateId: string;
  name: string;
  description: string;
}

export interface AgentListItem {
  agentId: string;
  name: string;
  description: string;
  invokeMode: AgentInvokeMode;
  status: AgentStatus;
  verifiedAt: string | null;
  lastVerificationPassed: boolean | null;
  canSubmitEvaluation: boolean;
  canVerify: boolean;
  canArchive: boolean;
  canCopyCreate: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AgentVerificationMessage {
  code: string;
  message: string;
}

export interface AgentVerificationSummary {
  passed: boolean;
  warnings: AgentVerificationMessage[];
  errors: AgentVerificationMessage[];
}

export interface AgentDetail
  extends Omit<
    AgentDefaultConfig,
    "auth"
  > {
  agentId: string;
  templateId: string;
  name: string;
  description: string;
  status: AgentStatus;
  auth: AgentAuthPublicSummary;
  verifiedAt: string | null;
  lastVerification: AgentVerificationSummary | null;
  actions: {
    canSubmitEvaluation: boolean;
    canVerify: boolean;
    canArchive: boolean;
    canCopyCreate: boolean;
  };
  createdAt: string;
  updatedAt: string;
}

export interface AgentCreateResponse {
  agentId: string;
  name: string;
  invokeMode: AgentInvokeMode;
  status: AgentStatus;
  verifiedAt: string | null;
  lastVerificationPassed: boolean | null;
  createdAt: string;
  updatedAt: string;
}

export interface AgentVerifyResponse {
  agentId: string;
  passed: boolean;
  status: AgentStatus;
  verifiedAt: string;
  warnings: AgentVerificationMessage[];
  errors: AgentVerificationMessage[];
}

export interface AgentArchiveResponse {
  agentId: string;
  status: AgentStatus;
  updatedAt: string;
}
