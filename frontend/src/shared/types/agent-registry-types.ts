export type AgentInvokeMode = "sync_response" | "submit_poll";
export type AgentTaskRenderMode = "goal_only" | "goal_with_entry_url";
export type AgentStatus = "draft" | "verifying" | "active" | "invalid" | "archived";
export type AgentAuthType = "none" | "bearer" | "api_key_header" | "custom_header";
export type AgentCancelMethod = "POST" | "DELETE" | "PATCH";

export interface AgentConnectionConfig {
  baseUrl: string;
  invokePath: string;
  resultPathTemplate?: string;
  cancelPathTemplate?: string | null;
  cancelMethod?: AgentCancelMethod;
  cancelRequestBody?: Record<string, unknown> | null;
  requestTimeoutSeconds: number;
  pollIntervalSeconds: number;
  pollTimeoutSeconds: number;
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
  success?: string;
  finalAnswer?: string;
  errorMessage?: string;
}

export interface AgentRequestOptions {
  structuredOutput: {
    supported: boolean;
    fieldAlias: string;
  };
}

export interface AgentCredentialConfig {
  token?: string;
  headerName?: string;
  secret?: string;
  [key: string]: unknown;
}

export interface AgentCreateAuthConfig {
  type: AgentAuthType;
  config: Record<string, string>;
}

export interface AgentTemplateAuthConfig {
  type: AgentAuthType;
  config: AgentCredentialConfig;
}

export interface AgentCreatePayload {
  templateId?: string | null;
  name: string;
  description?: string | null;
  invokeMode: AgentInvokeMode;
  maxConcurrency: number;
  connection: AgentConnectionConfig;
  auth: AgentCreateAuthConfig;
  platformInputMapping: AgentInputMapping;
  taskRenderMode: AgentTaskRenderMode;
  customRequestBody: Record<string, unknown>;
  requestOptions: AgentRequestOptions;
  platformOutputMapping: AgentOutputMapping;
  terminalStatuses: string[];
  successStatuses: string[];
}

export interface AgentListItem {
  agentId: string;
  name: string;
  description?: string | null;
  invokeMode: AgentInvokeMode;
  maxConcurrency: number;
  status: AgentStatus;
  verifiedAt?: string | null;
  lastVerificationPassed?: boolean | null;
  canSubmitEvaluation?: boolean | null;
  canVerify?: boolean | null;
  canArchive?: boolean | null;
  canCopyCreate?: boolean | null;
  createdAt: string;
  updatedAt: string;
}

export type AgentCreateResponse = AgentListItem;

export interface AgentAuthPublic {
  type: AgentAuthType;
  hasCredential: boolean;
  publicConfig?: AgentCredentialConfig | null;
  config?: AgentCredentialConfig | null;
}

export interface AgentActions {
  canSubmitEvaluation: boolean;
  canVerify: boolean;
  canArchive: boolean;
  canCopyCreate: boolean;
}

export interface AgentVerificationMessage {
  code: string;
  message: string;
}

export interface AgentVerificationState {
  passed: boolean;
  warnings: AgentVerificationMessage[];
  errors: AgentVerificationMessage[];
}

export interface AgentDetail
  extends Omit<
    AgentCreatePayload,
    "auth" | "templateId" | "description" | "successStatuses" | "terminalStatuses"
  > {
  agentId: string;
  templateId?: string | null;
  description?: string | null;
  auth: AgentAuthPublic;
  status: AgentStatus;
  terminalStatuses: string[];
  successStatuses: string[];
  verifiedAt?: string | null;
  lastVerification?: AgentVerificationState | null;
  actions: AgentActions;
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
  status: Extract<AgentStatus, "archived">;
  updatedAt: string;
}

export interface AgentTemplateDefaultConfig {
  invokeMode: AgentInvokeMode;
  maxConcurrency: number;
  connection: AgentConnectionConfig;
  auth: AgentTemplateAuthConfig;
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
  level: string;
  tags: string[];
  defaultConfig: AgentTemplateDefaultConfig;
}
