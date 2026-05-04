import {
  normalizeDifficulty,
  normalizeMaxSteps,
  normalizeTimeoutMinutes,
} from "@/modules/submission/model/parameter-validator";
import type {
  PendingSubmitRequest,
  SubmitFormState,
  SubmitMetaResponse,
  SubmitParameters,
} from "@/shared/types/agent-types";

export const normalizeSubmitDraftParameters = (
  form: SubmitFormState,
  meta: SubmitMetaResponse,
): SubmitParameters => ({
  difficulty: normalizeDifficulty(form.parameters.difficulty, meta.difficulty),
  timeoutMinutes: normalizeTimeoutMinutes(
    form.parameters.timeoutMinutes,
    meta.timeoutMinutes,
  ),
  maxSteps: normalizeMaxSteps(form.parameters.maxSteps, meta.maxSteps),
});

export const shouldClearPendingSubmitRequest = (
  pendingRequest: PendingSubmitRequest | null,
  payloadDigest: string,
): boolean =>
  Boolean(
    pendingRequest &&
    payloadDigest &&
    pendingRequest.payloadDigest !== payloadDigest,
  );
