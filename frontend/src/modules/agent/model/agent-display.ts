import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";
import type {
  AgentInvokeMode,
  AgentListItem,
  AgentStatus,
} from "@/shared/types/agent-registry-types";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

export const getAgentStatusLabel = (
  status: AgentStatus,
  t: AppTranslator = translateRuntimeMessage,
): string => {
  switch (status) {
    case "draft":
      return t("agent.display.status.draft");
    case "verifying":
      return t("agent.display.status.verifying");
    case "active":
      return t("agent.display.status.active");
    case "invalid":
      return t("agent.display.status.invalid");
    case "archived":
      return t("agent.display.status.archived");
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

export const getAgentStatusIcon = (status: AgentStatus): AppIconName => {
  switch (status) {
    case "draft":
      return "app:status.draft";
    case "verifying":
      return "app:status.verifying";
    case "active":
      return "app:status.active";
    case "invalid":
      return "app:status.invalid";
    case "archived":
      return "app:status.archived";
  }
};

export const getInvokeModeLabel = (
  mode: AgentInvokeMode,
  t: AppTranslator = translateRuntimeMessage,
): string =>
  mode === "submit_poll"
    ? t("agent.display.invokeModes.submitPoll")
    : t("agent.display.invokeModes.syncResponse");

export const getAgentSubmitDisabledReason = (
  agent: AgentListItem,
  t: AppTranslator = translateRuntimeMessage,
): string => {
  if (agent.status === "active") {
    return t("agent.display.disabledReasons.active");
  }

  if (agent.status === "draft") {
    return t("agent.display.disabledReasons.draft");
  }

  if (agent.status === "verifying") {
    return t("agent.display.disabledReasons.verifying");
  }

  if (agent.status === "invalid") {
    return t("agent.display.disabledReasons.invalid");
  }

  return t("agent.display.disabledReasons.archived");
};

export const canVerifyAgent = (status: AgentStatus): boolean =>
  status === "draft" || status === "active" || status === "invalid";

export const canArchiveAgent = (status: AgentStatus): boolean =>
  status === "draft" || status === "active" || status === "invalid";
