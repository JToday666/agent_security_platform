import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";
import { getInvokeModeLabel } from "@/modules/agent/model/agent-display";
import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import type {
  AgentAuthType,
  AgentDetail,
  AgentVerificationMessage,
} from "@/shared/types/agent-registry-types";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

export interface AgentDetailTextItem {
  label: string;
  value: string;
  kind?: "text" | "status";
}

export interface AgentMappingDisplayItem {
  label: string;
  sourceLabel: string;
  source: string;
  targetLabel: string;
  target: string;
  empty: boolean;
}

export interface AgentVerificationMessageGroup {
  label: string;
  tone: "warning" | "danger";
  messages: AgentVerificationMessage[];
}

const getAuthLabelKey = (authType: AgentAuthType): string => {
  switch (authType) {
    case "none":
      return "agent.auth.none";
    case "bearer":
      return "agent.auth.bearer";
    case "api_key_header":
      return "agent.auth.apiKeyHeader";
    case "custom_header":
      return "agent.auth.customHeader";
  }
};

const displayValue = (value: unknown): string => {
  if (typeof value === "number") {
    return String(value);
  }

  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }

  return "-";
};

const toMappingValue = (
  value: unknown,
  t: AppTranslator,
): { text: string; empty: boolean } => {
  if (typeof value === "string" && value.trim()) {
    return { text: value.trim(), empty: false };
  }

  if (typeof value === "number") {
    return { text: String(value), empty: false };
  }

  return { text: t("agent.mapping.empty"), empty: true };
};

export const formatAgentVerificationLabel = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): string => {
  if (!detail.verifiedAt) {
    return t("agent.verification.notVerified");
  }

  const result =
    detail.lastVerification?.passed === true
      ? t("agent.verification.passed")
      : detail.lastVerification?.passed === false
        ? t("agent.verification.failed")
        : t("agent.common.unknown");
  return `${formatDateTimeLabel(detail.verifiedAt)} · ${result}`;
};

export const getAgentAuthLabel = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): string => t(getAuthLabelKey(detail.auth.type));

export const getAgentAuthHeaderName = (detail: AgentDetail): string => {
  const headerName = detail.auth.publicConfig?.headerName;
  return typeof headerName === "string" ? headerName : "";
};

export const getAgentVerificationResultLabel = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): string =>
  detail.lastVerification?.passed
    ? t("agent.verification.passedResult")
    : t("agent.verification.failedResult");

export const getAgentVerificationResultIcon = (detail: AgentDetail): AppIconName =>
  detail.lastVerification?.passed
    ? "app:status.completed"
    : "app:status.warning";

export const buildAgentSummaryItems = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): AgentDetailTextItem[] => [
  { label: t("agent.detail.items.status"), value: detail.status, kind: "status" },
  { label: t("agent.detail.items.invokeMode"), value: getInvokeModeLabel(detail.invokeMode, t) },
  { label: t("agent.detail.items.recentVerification"), value: formatAgentVerificationLabel(detail, t) },
  { label: t("agent.detail.items.updatedAt"), value: formatDateTimeLabel(detail.updatedAt) },
];

export const buildAgentConnectionItems = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): AgentDetailTextItem[] => {
  const { connection } = detail;
  return [
    { label: t("agent.detail.items.connectionBaseUrl"), value: displayValue(connection.baseUrl) },
    { label: t("agent.detail.items.taskPath"), value: displayValue(connection.invokePath) },
    {
      label: t("agent.detail.items.resultPathTemplate"),
      value: displayValue(connection.resultPathTemplate),
    },
    { label: t("agent.detail.items.requestTimeout"), value: t("agent.common.seconds", { value: connection.requestTimeoutSeconds }) },
    { label: t("agent.detail.items.pollInterval"), value: t("agent.common.seconds", { value: connection.pollIntervalSeconds }) },
    { label: t("agent.detail.items.pollTimeout"), value: t("agent.common.seconds", { value: connection.pollTimeoutSeconds }) },
  ];
};

export const buildAgentAuthItems = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): AgentDetailTextItem[] => [
  { label: t("agent.detail.items.authMethod"), value: getAgentAuthLabel(detail, t) },
  ...(getAgentAuthHeaderName(detail)
    ? [{ label: t("agent.detail.items.authHeaderName"), value: getAgentAuthHeaderName(detail) }]
    : []),
  {
    label: t("agent.detail.items.credentialStatus"),
    value: detail.auth.hasCredential
      ? t("agent.common.configured")
      : t("agent.common.notConfigured"),
  },
];

export const buildAgentInputMappingItems = (
  value: Record<string, unknown>,
  t: AppTranslator = translateRuntimeMessage,
): AgentMappingDisplayItem[] =>
  Object.entries(value).map(([key, item]) => {
    const target = toMappingValue(item, t);
    return {
      label: key,
      sourceLabel: t("agent.mapping.platformField"),
      source: key,
      targetLabel: t("agent.mapping.agentField"),
      target: target.text,
      empty: target.empty,
    };
  });

export const buildAgentOutputMappingItems = (
  value: Record<string, unknown>,
  t: AppTranslator = translateRuntimeMessage,
): AgentMappingDisplayItem[] =>
  Object.entries(value).map(([key, item]) => {
    const source = toMappingValue(item, t);
    return {
      label: key,
      sourceLabel: t("agent.mapping.responsePath"),
      source: source.text,
      targetLabel: t("agent.mapping.platformField"),
      target: key,
      empty: source.empty,
    };
  });

export const buildAgentStatusItems = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): AgentDetailTextItem[] => [
  {
    label: t("agent.detail.items.terminalStatuses"),
    value: detail.terminalStatuses.join(t("agent.common.listSeparator")) || "-",
  },
  {
    label: t("agent.detail.items.successStatuses"),
    value: detail.successStatuses.join(t("agent.common.listSeparator")) || "-",
  },
];

export const buildAgentCustomRequestBodyJson = (detail: AgentDetail): string =>
  JSON.stringify(detail.customRequestBody ?? {}, null, 2);

export const buildAgentVerificationStatItems = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): AgentDetailTextItem[] => {
  const verification = detail.lastVerification;
  if (!verification) {
    return [];
  }

  return [
    {
      label: t("agent.verification.time"),
      value: detail.verifiedAt
        ? formatDateTimeLabel(detail.verifiedAt)
        : t("agent.common.unknown"),
    },
    { label: t("agent.verification.errors"), value: String(verification.errors.length) },
    { label: t("agent.verification.warnings"), value: String(verification.warnings.length) },
  ];
};

export const buildAgentVerificationMessageGroups = (
  detail: AgentDetail,
  t: AppTranslator = translateRuntimeMessage,
): AgentVerificationMessageGroup[] => {
  const verification = detail.lastVerification;
  if (!verification) {
    return [];
  }

  return [
    {
      label: t("agent.verification.errors"),
      tone: "danger" as const,
      messages: verification.errors,
    },
    {
      label: t("agent.verification.warnings"),
      tone: "warning" as const,
      messages: verification.warnings,
    },
  ].filter((group) => group.messages.length > 0);
};
