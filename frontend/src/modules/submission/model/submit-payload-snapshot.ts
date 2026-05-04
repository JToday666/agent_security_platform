import {
  normalizeDifficulty,
  normalizeMaxSteps,
  normalizeTimeoutMinutes,
} from "@/modules/submission/model/parameter-validator";
import type {
  SubmitAgentPayload,
  SubmitFormState,
  SubmitMetaResponse,
} from "@/shared/types/agent-types";

export interface SubmitPayloadSnapshot {
  submitMethod: SubmitAgentPayload["submitMethod"];
  agentId: string;
  parameters: SubmitAgentPayload["parameters"];
  publicToLeaderboard: boolean;
  datasetIds: string[];
}

export const buildSubmitPayloadSnapshot = (
  form: SubmitFormState | null,
  meta: SubmitMetaResponse | null,
): SubmitPayloadSnapshot | null => {
  if (!form || !meta) {
    return null;
  }

  const datasetIds = Array.from(new Set(form.selectedDatasetIds)).sort();

  return {
    submitMethod: form.submitMethod,
    agentId: form.submitMethod === "api" ? form.agentId.trim() : "",
    parameters: {
      difficulty: normalizeDifficulty(
        form.parameters.difficulty,
        meta.difficulty,
      ),
      timeoutMinutes: normalizeTimeoutMinutes(
        form.parameters.timeoutMinutes,
        meta.timeoutMinutes,
      ),
      maxSteps: normalizeMaxSteps(form.parameters.maxSteps, meta.maxSteps),
    },
    publicToLeaderboard: Boolean(form.publicToLeaderboard),
    datasetIds,
  };
};

export const buildSubmitPayloadDigest = (
  snapshot: SubmitPayloadSnapshot | null,
): string => (snapshot ? JSON.stringify(snapshot) : "");

export const buildSubmitPayloadFromSnapshot = (
  snapshot: SubmitPayloadSnapshot,
  form: SubmitFormState,
  requestId: string,
): SubmitAgentPayload => ({
  submitMethod: snapshot.submitMethod,
  agentId: snapshot.submitMethod === "api" ? snapshot.agentId : null,
  docker:
    snapshot.submitMethod === "docker"
      ? {
          imageUri: form.docker.imageUri.trim(),
          command: form.docker.command.trim(),
          env: {},
        }
      : null,
  parameters: snapshot.parameters,
  publicToLeaderboard: snapshot.publicToLeaderboard,
  selectedDatasetIds: snapshot.datasetIds,
  requestId,
});
