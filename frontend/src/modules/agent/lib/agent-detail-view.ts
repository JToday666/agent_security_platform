import { getInvokeModeLabel } from "@/modules/agent/model/agent-display";
import { formatDateTimeLabel } from "@/modules/dataset/lib/dataset-utils";
import type {
  AgentAuthType,
  AgentDetail,
  AgentVerificationMessage,
} from "@/shared/types/agent-registry-types";

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

const AUTH_LABEL_MAP: Record<AgentAuthType, string> = {
  none: "不使用鉴权",
  bearer: "Bearer Token",
  api_key_header: "API Key Header",
  custom_header: "自定义 Header",
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

const toMappingValue = (value: unknown): { text: string; empty: boolean } => {
  if (typeof value === "string" && value.trim()) {
    return { text: value.trim(), empty: false };
  }

  if (typeof value === "number") {
    return { text: String(value), empty: false };
  }

  return { text: "未配置", empty: true };
};

export const formatAgentVerificationLabel = (detail: AgentDetail): string => {
  if (!detail.verifiedAt) {
    return "未验证";
  }

  const result =
    detail.lastVerification?.passed === true
      ? "通过"
      : detail.lastVerification?.passed === false
        ? "失败"
        : "未知";
  return `${formatDateTimeLabel(detail.verifiedAt)} · ${result}`;
};

export const getAgentAuthLabel = (detail: AgentDetail): string =>
  AUTH_LABEL_MAP[detail.auth.type];

export const getAgentAuthHeaderName = (detail: AgentDetail): string => {
  const headerName = detail.auth.publicConfig?.headerName;
  return typeof headerName === "string" ? headerName : "";
};

export const getAgentVerificationResultLabel = (detail: AgentDetail): string =>
  detail.lastVerification?.passed ? "验证通过" : "验证失败";

export const getAgentVerificationResultIcon = (detail: AgentDetail): string =>
  detail.lastVerification?.passed
    ? "lucide:circle-check-big"
    : "lucide:triangle-alert";

export const buildAgentSummaryItems = (
  detail: AgentDetail,
): AgentDetailTextItem[] => [
  { label: "状态", value: detail.status, kind: "status" },
  { label: "调用模式", value: getInvokeModeLabel(detail.invokeMode) },
  { label: "最近验证", value: formatAgentVerificationLabel(detail) },
  { label: "更新时间", value: formatDateTimeLabel(detail.updatedAt) },
];

export const buildAgentConnectionItems = (
  detail: AgentDetail,
): AgentDetailTextItem[] => {
  const { connection } = detail;
  return [
    { label: "服务根地址", value: displayValue(connection.baseUrl) },
    { label: "提交任务路径", value: displayValue(connection.invokePath) },
    {
      label: "结果路径模板",
      value: displayValue(connection.resultPathTemplate),
    },
    { label: "请求超时", value: `${connection.requestTimeoutSeconds} 秒` },
    { label: "轮询间隔", value: `${connection.pollIntervalSeconds} 秒` },
    { label: "轮询总超时", value: `${connection.pollTimeoutSeconds} 秒` },
  ];
};

export const buildAgentAuthItems = (
  detail: AgentDetail,
): AgentDetailTextItem[] => [
  { label: "鉴权方式", value: getAgentAuthLabel(detail) },
  ...(getAgentAuthHeaderName(detail)
    ? [{ label: "Header 名称", value: getAgentAuthHeaderName(detail) }]
    : []),
  {
    label: "凭据状态",
    value: detail.auth.hasCredential ? "已配置" : "未配置",
  },
];

export const buildAgentInputMappingItems = (
  value: Record<string, unknown>,
): AgentMappingDisplayItem[] =>
  Object.entries(value).map(([key, item]) => {
    const target = toMappingValue(item);
    return {
      label: key,
      sourceLabel: "平台字段",
      source: key,
      targetLabel: "Agent 字段",
      target: target.text,
      empty: target.empty,
    };
  });

export const buildAgentOutputMappingItems = (
  value: Record<string, unknown>,
): AgentMappingDisplayItem[] =>
  Object.entries(value).map(([key, item]) => {
    const source = toMappingValue(item);
    return {
      label: key,
      sourceLabel: "响应路径",
      source: source.text,
      targetLabel: "平台字段",
      target: key,
      empty: source.empty,
    };
  });

export const buildAgentStatusItems = (
  detail: AgentDetail,
): AgentDetailTextItem[] => [
  {
    label: "终态",
    value: detail.terminalStatuses.join("、") || "-",
  },
  {
    label: "成功态",
    value: detail.successStatuses.join("、") || "-",
  },
];

export const buildAgentCustomRequestBodyJson = (detail: AgentDetail): string =>
  JSON.stringify(detail.customRequestBody ?? {}, null, 2);

export const buildAgentVerificationStatItems = (
  detail: AgentDetail,
): AgentDetailTextItem[] => {
  const verification = detail.lastVerification;
  if (!verification) {
    return [];
  }

  return [
    {
      label: "验证时间",
      value: detail.verifiedAt
        ? formatDateTimeLabel(detail.verifiedAt)
        : "未知",
    },
    { label: "错误", value: String(verification.errors.length) },
    { label: "警告", value: String(verification.warnings.length) },
  ];
};

export const buildAgentVerificationMessageGroups = (
  detail: AgentDetail,
): AgentVerificationMessageGroup[] => {
  const verification = detail.lastVerification;
  if (!verification) {
    return [];
  }

  return [
    {
      label: "错误",
      tone: "danger" as const,
      messages: verification.errors,
    },
    {
      label: "警告",
      tone: "warning" as const,
      messages: verification.warnings,
    },
  ].filter((group) => group.messages.length > 0);
};
