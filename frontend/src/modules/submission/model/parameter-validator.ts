import type {
  LeaderboardDisplayMode,
  RangeMeta,
  SubmitAgentPayload,
  SubmitFieldErrors,
  SubmitMetaResponse,
} from "@/shared/types/agent-types";

export const MAX_SUBMIT_DATASET_COUNT = 100;
const REQUEST_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/;

const countDecimals = (value: number): number => {
  const text = value.toString();
  const index = text.indexOf(".");
  return index === -1 ? 0 : text.length - index - 1;
};

const clamp = (value: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, value));

const normalizeToStep = (value: number, meta: RangeMeta): number => {
  const precision = Math.max(countDecimals(meta.step), countDecimals(meta.min));
  const stepped =
    Math.round((value - meta.min) / meta.step) * meta.step + meta.min;

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
  const stepped = (value - meta.min) / meta.step;
  return Number.isInteger(Number(stepped.toFixed(6)));
};

export const getRangeSoftWarning = (
  value: number,
  meta: RangeMeta,
  fallbackThreshold = meta.max,
): string => {
  const threshold = meta.recommendedMax ?? fallbackThreshold;

  if (value <= threshold) {
    return "";
  }

  return `当前设置高于建议值 ${threshold}，可能增加等待和执行耗时。`;
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
  datasetIds: string[];
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
  validDatasetIds: string[],
  activeAgentIds: string[] = [],
): ValidationResult => {
  const errors: string[] = [];
  const fieldErrors: SubmitFieldErrors = {};

  if (!meta.supportedMethods.includes(payload.submitMethod)) {
    errors.push("当前提交方式不可用。");
  }

  if (payload.submitMethod === "api") {
    const agentId = payload.agentId?.trim() ?? "";
    if (!agentId || !activeAgentIds.includes(agentId)) {
      errors.push("请选择可评测智能体。");
      fieldErrors.agentId = "请选择可评测智能体";
    }
  }

  if (payload.submitMethod === "docker") {
    errors.push("Docker 提交方式正在开发。");
    fieldErrors.docker = "该功能正在开发";
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
    errors.push("攻击难度超出允许范围。");
  }

  if (
    timeoutOutOfRange ||
    timeoutMinutes !==
      normalizeTimeoutMinutes(timeoutMinutes, meta.timeoutMinutes) ||
    !Number.isInteger(timeoutMinutes) ||
    !isStepAligned(timeoutMinutes, meta.timeoutMinutes)
  ) {
    errors.push("超时时间超出允许范围。");
  }

  if (
    maxStepsOutOfRange ||
    maxSteps !== normalizeMaxSteps(maxSteps, meta.maxSteps) ||
    !Number.isInteger(maxSteps) ||
    !isStepAligned(maxSteps, meta.maxSteps)
  ) {
    errors.push("最大步数超出允许范围。");
  }

  if (payload.selectedDatasetIds.length === 0) {
    errors.push("请至少选择一个评测项。");
    fieldErrors.selectedDatasetIds = "请至少选择一个评测项";
  }

  const uniqueDatasetIds = Array.from(new Set(payload.selectedDatasetIds));
  if (uniqueDatasetIds.length !== payload.selectedDatasetIds.length) {
    errors.push("评测项选择中存在重复数据集，请刷新后重试。");
    fieldErrors.selectedDatasetIds = "评测项选择中存在重复数据集";
  }

  if (uniqueDatasetIds.length > MAX_SUBMIT_DATASET_COUNT) {
    errors.push(`评测项数量不能超过 ${MAX_SUBMIT_DATASET_COUNT} 个。`);
    fieldErrors.selectedDatasetIds = `最多只能选择 ${MAX_SUBMIT_DATASET_COUNT} 个评测项`;
  }

  const validDatasetIdSet = new Set(validDatasetIds);
  const hasInvalidDataset = uniqueDatasetIds.some(
    (item) => !validDatasetIdSet.has(item),
  );

  if (hasInvalidDataset) {
    errors.push("已选择的评测项里包含失效项，请刷新后重试。");
    fieldErrors.selectedDatasetIds = "已选择的评测项里包含失效项";
  }

  if (!REQUEST_ID_PATTERN.test(payload.requestId.trim())) {
    errors.push("requestId 格式不正确，请重试。");
    fieldErrors.requestId = "requestId 格式不正确";
  }

  if (!meta.leaderboardDisplayMode.options.includes(payload.leaderboardDisplayMode)) {
    errors.push("榜单展示方式不可用。");
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
    datasetIds: payload.selectedDatasetIds,
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
