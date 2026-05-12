import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";
import { getInvokeModeLabel } from "@/modules/agent/model/agent-display";
import type { AgentListItem } from "@/shared/types/agent-registry-types";

export interface SubmitAgentOption {
  label: string;
  value: string;
}

export const filterAvailableSubmitAgents = (
  agents: AgentListItem[],
): AgentListItem[] =>
  agents.filter(
    (agent) => agent.status === "active" && agent.canSubmitEvaluation,
  );

export const buildSubmitAgentOptions = (
  agents: AgentListItem[],
  t: AppTranslator = translateRuntimeMessage,
): SubmitAgentOption[] =>
  filterAvailableSubmitAgents(agents).map((agent) => ({
    label: `${agent.name} · ${getInvokeModeLabel(agent.invokeMode, t)}`,
    value: agent.agentId,
  }));
