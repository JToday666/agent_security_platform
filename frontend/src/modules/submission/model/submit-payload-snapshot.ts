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
  leaderboardDisplayMode: SubmitAgentPayload["leaderboardDisplayMode"];
  attackScenarioId: string;
  evaluationItemIds: string[];
}

export const buildSubmitPayloadSnapshot = (
  form: SubmitFormState | null,
  meta: SubmitMetaResponse | null,
): SubmitPayloadSnapshot | null => {
  if (!form || !meta) {
    return null;
  }

  const evaluationItemIds = Array.from(
    new Set(form.selectedEvaluationItemIds),
  ).sort();

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
    leaderboardDisplayMode: meta.leaderboardDisplayMode.options.includes(
      form.leaderboardDisplayMode,
    )
      ? form.leaderboardDisplayMode
      : meta.leaderboardDisplayMode.default,
    attackScenarioId: form.selectedAttackScenarioId,
    evaluationItemIds,
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
  leaderboardDisplayMode: snapshot.leaderboardDisplayMode,
  attackScenarioId: snapshot.attackScenarioId,
  evaluationItemIds: snapshot.evaluationItemIds,
  requestId,
});
