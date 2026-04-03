import type {
  SubmitAgentApiPayload,
  SubmitAgentPayload,
  SubmitMetaApiResponse,
  SubmitMetaResponse,
} from "@/types/AgentTypes";

export const normalizeSubmitMeta = (
  payload: SubmitMetaApiResponse,
): SubmitMetaResponse => {
  if ("parameterMeta" in payload) {
    return {
      supportedMethods: payload.supportedMethods,
      difficulty: payload.parameterMeta.difficulty,
      timeoutMinutes: {
        ...payload.parameterMeta.timeoutMinutes,
        recommendedMax:
          payload.parameterMeta.timeoutMinutes.recommendedMax ?? 20,
      },
      retryEnabled: payload.parameterMeta.retryEnabled,
      publicToLeaderboard: payload.parameterMeta.publicToLeaderboard,
    };
  }

  return {
    ...payload,
    timeoutMinutes: {
      ...payload.timeoutMinutes,
      recommendedMax: payload.timeoutMinutes.recommendedMax ?? 20,
    },
  };
};

export const buildSubmitAgentApiPayload = (
  payload: SubmitAgentPayload,
): SubmitAgentApiPayload => ({
  ...payload,
  datasetIds: payload.selectedDatasetIds,
});
