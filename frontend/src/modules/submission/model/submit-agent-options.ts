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
): SubmitAgentOption[] =>
  filterAvailableSubmitAgents(agents).map((agent) => ({
    label: `${agent.name} · ${getInvokeModeLabel(agent.invokeMode)}`,
    value: agent.agentId,
  }));
