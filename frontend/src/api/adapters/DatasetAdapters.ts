import type {
  SubmitAgentApiPayload,
  SubmitAgentPayload,
} from "@/types/AgentTypes";

export const buildSubmitAgentApiPayload = (
  payload: SubmitAgentPayload,
): SubmitAgentApiPayload => ({
  agentName: payload.agentName,
  description: payload.description,
  submitMethod: payload.submitMethod,
  api: payload.api,
  docker: payload.docker,
  parameters: payload.parameters,
  publicToLeaderboard: payload.publicToLeaderboard,
  requestId: payload.requestId,
  datasetIds: payload.selectedDatasetIds,
});
