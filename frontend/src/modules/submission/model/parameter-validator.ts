import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";
import type {
  LeaderboardDisplayMode,
  RangeMeta,
  SubmitAgentPayload,
  SubmitFieldErrors,
  SubmitMetaResponse,
} from "@/shared/types/agent-types";

export const MAX_SUBMIT_EVALUATION_ITEM_COUNT = 100;
const REQUEST_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/;

const countDecimals = (value: number): number => {
  const text = value.toString();
  const index = text.indexOf(".");
  return index === -1 ? 0 : text.length - index - 1;
};

const clamp = (value: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, value));

const resolvePositiveStep = (value: number): number =>
  Number.isFinite(value) && value > 0 ? value : 1;

const normalizeToStep = (value: number, meta: RangeMeta): number => {
  const step = resolvePositiveStep(meta.step);
  const precision = Math.max(countDecimals(step), countDecimals(meta.min));
  const stepped = Math.round((value - meta.min) / step) * step + meta.min;

  return Number(stepped.toFixed(Math.max(precision, 0)));
};

const toFiniteNumber = (value: unknown, fallback: number): number => {
  const normalized =
    typeof value === "number" ? value : Number.parseFloat(String(value));

  return Number.isFinite(normalized) ? normalized : fallback;
};

export const normalizeDifficulty = (
  value: unknown,
  meta: RangeMeta,
): number => {
  const clamped = clamp(
    toFiniteNumber(value, meta.default),
    meta.min,
    meta.max,
  );
  return Number(normalizeToStep(clamped, meta).toFixed(1));
};

export const normalizeTimeoutMinutes = (
  value: unknown,
  meta: RangeMeta,
): number => {
  const clamped = clamp(
    toFiniteNumber(value, meta.default),
    meta.min,
    meta.max,
  );
  return Math.round(normalizeToStep(clamped, meta));
};

export const normalizeMaxSteps = (value: unknown, meta: RangeMeta): number => {
  const clamped = clamp(
    toFiniteNumber(value, meta.default),
    meta.min,
    meta.max,
  );
  return Math.round(normalizeToStep(clamped, meta));
};

export const isStepAligned = (value: number, meta: RangeMeta): boolean => {
  const step = resolvePositiveStep(meta.step);
  const stepped = (value - meta.min) / step;
  return Number.isInteger(Number(stepped.toFixed(6)));
};

export const getRangeSoftWarning = (
  value: number,
  meta: RangeMeta,
  fallbackThreshold = meta.max,
  t: AppTranslator = translateRuntimeMessage,
): string => {
  const threshold = meta.recommendedMax ?? fallbackThreshold;

  if (value <= threshold) {
    return "";
  }

  return t("submission.parameters.softWarning", { threshold });
};

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  fieldErrors: SubmitFieldErrors;
}

export interface EvaluationCreatePayload {
  requestId: string;
  submitMethod: "api" | "docker";
  agentId?: string;
  docker?: {
    imageUri: string;
    command: string;
    env: Record<string, string>;
  };
  attackScenarioId: string;
  evaluationItemIds: string[];
  parameters: {
    difficulty: number;
    timeoutMinutes: number;
    maxSteps: number;
  };
  leaderboardDisplayMode: LeaderboardDisplayMode;
}

export const isValidHttpUrl = (value: string): boolean => {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
};

export const validateSubmitPayload = (
  payload: SubmitAgentPayload,
  meta: SubmitMetaResponse,
  validEvaluationItemIds: string[],
  activeAgentIds: string[] = [],
  t: AppTranslator = translateRuntimeMessage,
): ValidationResult => {
  const errors: string[] = [];
  const fieldErrors: SubmitFieldErrors = {};

  if (!meta.supportedMethods.includes(payload.submitMethod)) {
    errors.push(t("submission.validation.methodUnavailable"));
  }

  if (payload.submitMethod === "api") {
    const agentId = payload.agentId?.trim() ?? "";
    if (!agentId || !activeAgentIds.includes(agentId)) {
      errors.push(t("submission.validation.agentRequired"));
      fieldErrors.agentId = t("submission.validation.agentRequiredField");
    }
  }

  if (payload.submitMethod === "docker") {
    errors.push(t("submission.validation.dockerDeveloping"));
    fieldErrors.docker = t("submission.validation.dockerDevelopingField");
  }

  const { difficulty, timeoutMinutes, maxSteps } = payload.parameters;
  const difficultyOutOfRange =
    difficulty < meta.difficulty.min || difficulty > meta.difficulty.max;
  const timeoutOutOfRange =
    timeoutMinutes < meta.timeoutMinutes.min ||
    timeoutMinutes > meta.timeoutMinutes.max;
  const maxStepsOutOfRange =
    maxSteps < meta.maxSteps.min || maxSteps > meta.maxSteps.max;

  if (
    difficultyOutOfRange ||
    difficulty !== normalizeDifficulty(difficulty, meta.difficulty) ||
    !isStepAligned(difficulty, meta.difficulty)
  ) {
    errors.push(t("submission.validation.difficultyRange"));
  }

  if (
    timeoutOutOfRange ||
    timeoutMinutes !==
      normalizeTimeoutMinutes(timeoutMinutes, meta.timeoutMinutes) ||
    !Number.isInteger(timeoutMinutes) ||
    !isStepAligned(timeoutMinutes, meta.timeoutMinutes)
  ) {
    errors.push(t("submission.validation.timeoutRange"));
  }

  if (
    maxStepsOutOfRange ||
    maxSteps !== normalizeMaxSteps(maxSteps, meta.maxSteps) ||
    !Number.isInteger(maxSteps) ||
    !isStepAligned(maxSteps, meta.maxSteps)
  ) {
    errors.push(t("submission.validation.maxStepsRange"));
  }

  if (!payload.attackScenarioId.trim()) {
    errors.push(t("submission.validation.attackScenarioRequired"));
    fieldErrors.selectedEvaluationItemIds = t(
      "submission.validation.attackScenarioRequiredField",
    );
  }

  if (payload.evaluationItemIds.length === 0) {
    errors.push(t("submission.validation.selectedEvaluationItemRequired"));
    fieldErrors.selectedEvaluationItemIds = t(
      "submission.validation.selectedEvaluationItemRequiredField",
    );
  }

  const uniqueEvaluationItemIds = Array.from(new Set(payload.evaluationItemIds));
  if (uniqueEvaluationItemIds.length !== payload.evaluationItemIds.length) {
    errors.push(t("submission.validation.evaluationItemDuplicate"));
    fieldErrors.selectedEvaluationItemIds = t(
      "submission.validation.evaluationItemDuplicateField",
    );
  }

  if (uniqueEvaluationItemIds.length > MAX_SUBMIT_EVALUATION_ITEM_COUNT) {
    errors.push(
      t("submission.validation.evaluationItemLimit", {
        count: MAX_SUBMIT_EVALUATION_ITEM_COUNT,
      }),
    );
    fieldErrors.selectedEvaluationItemIds = t(
      "submission.validation.evaluationItemLimitField",
      { count: MAX_SUBMIT_EVALUATION_ITEM_COUNT },
    );
  }

  const validEvaluationItemIdSet = new Set(validEvaluationItemIds);
  const hasInvalidEvaluationItem = uniqueEvaluationItemIds.some(
    (item) => !validEvaluationItemIdSet.has(item),
  );

  if (hasInvalidEvaluationItem) {
    errors.push(t("submission.validation.evaluationItemInvalid"));
    fieldErrors.selectedEvaluationItemIds = t(
      "submission.validation.evaluationItemInvalidField",
    );
  }

  if (!REQUEST_ID_PATTERN.test(payload.requestId.trim())) {
    errors.push(t("submission.validation.requestIdInvalid"));
    fieldErrors.requestId = t("submission.validation.requestIdInvalidField");
  }

  if (
    !meta.leaderboardDisplayMode.options.includes(
      payload.leaderboardDisplayMode,
    )
  ) {
    errors.push(t("submission.validation.leaderboardModeUnavailable"));
  }

  return {
    valid: errors.length === 0,
    errors,
    fieldErrors,
  };
};

export const buildEvaluationCreatePayload = (
  payload: SubmitAgentPayload,
): EvaluationCreatePayload => {
  const basePayload = {
    requestId: payload.requestId,
    submitMethod: payload.submitMethod,
    attackScenarioId: payload.attackScenarioId,
    evaluationItemIds: payload.evaluationItemIds,
    parameters: {
      difficulty: payload.parameters.difficulty,
      timeoutMinutes: payload.parameters.timeoutMinutes,
      maxSteps: payload.parameters.maxSteps,
    },
    leaderboardDisplayMode: payload.leaderboardDisplayMode,
  } satisfies Omit<EvaluationCreatePayload, "agentId" | "docker">;

  if (payload.submitMethod === "api") {
    return {
      ...basePayload,
      agentId: payload.agentId?.trim() ?? "",
    };
  }

  return {
    ...basePayload,
    docker: payload.docker
      ? {
          imageUri: payload.docker.imageUri.trim(),
          command: payload.docker.command.trim(),
          env: payload.docker.env,
        }
      : {
          imageUri: "",
          command: "",
          env: {},
        },
  };
};
