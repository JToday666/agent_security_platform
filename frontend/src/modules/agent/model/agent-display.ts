import type {
  AgentInvokeMode,
  AgentListItem,
  AgentStatus,
} from "@/shared/types/agent-registry-types";

export const getAgentStatusLabel = (status: AgentStatus): string => {
  switch (status) {
    case "draft":
      return "待验证";
    case "verifying":
      return "验证中";
    case "active":
      return "可评测";
    case "invalid":
      return "验证失败";
    case "archived":
      return "已归档";
  }
};

export const getAgentStatusTone = (
  status: AgentStatus,
): "neutral" | "info" | "success" | "warning" | "danger" | "muted" => {
  switch (status) {
    case "draft":
      return "warning";
    case "verifying":
      return "info";
    case "active":
      return "success";
    case "invalid":
      return "danger";
    case "archived":
      return "muted";
  }
};

export const getAgentStatusIcon = (status: AgentStatus): string => {
  switch (status) {
    case "draft":
      return "lucide:clock-3";
    case "verifying":
      return "lucide:loader-circle";
    case "active":
      return "lucide:circle-check-big";
    case "invalid":
      return "lucide:triangle-alert";
    case "archived":
      return "lucide:archive";
  }
};

export const getInvokeModeLabel = (mode: AgentInvokeMode): string =>
  mode === "submit_poll" ? "提交轮询" : "同步响应";

export const getAgentSubmitDisabledReason = (agent: AgentListItem): string => {
  if (agent.status === "active") {
    return "";
  }

  if (agent.status === "draft") {
    return "该 Agent 尚未验证通过，不能提交评测。";
  }

  if (agent.status === "verifying") {
    return "该 Agent 正在验证中，暂不能提交评测。";
  }

  if (agent.status === "invalid") {
    return "该 Agent 验证失败，不能提交评测。";
  }

  return "已归档 Agent 不能提交评测。";
};

export const canVerifyAgent = (status: AgentStatus): boolean =>
  status === "draft" || status === "active" || status === "invalid";

export const canArchiveAgent = (status: AgentStatus): boolean =>
  status === "draft" || status === "active" || status === "invalid";
