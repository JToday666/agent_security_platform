import type {
  SubmitAgentPayload,
  SubmitMetaResponse,
} from "@/types/AgentTypes";
import {
  isStepAligned,
  normalizeDifficulty,
  normalizeTimeoutMinutes,
} from "@/utils/SubmitParameterUtils";

export interface ValidationResult {
  valid: boolean;
  errors: string[];
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
): ValidationResult => {
  const errors: string[] = [];

  if (!payload.agentName.trim()) {
    errors.push("请填写智能体名称。");
  }

  if (!meta.supportedMethods.includes(payload.submitMethod)) {
    errors.push("当前提交方式不可用。");
  }

  if (payload.submitMethod === "api") {
    if (!payload.api?.baseUrl.trim()) {
      errors.push("API 模式下必须填写服务地址。");
    } else if (!isValidHttpUrl(payload.api.baseUrl)) {
      errors.push("API 地址格式不正确。");
    }
  }

  if (payload.submitMethod === "docker" && !payload.docker?.imageUri.trim()) {
    errors.push("Docker 模式下必须填写镜像地址。");
  }

  const { difficulty, timeoutMinutes } = payload.parameters;
  const difficultyOutOfRange =
    difficulty < meta.difficulty.min || difficulty > meta.difficulty.max;
  const timeoutOutOfRange =
    timeoutMinutes < meta.timeoutMinutes.min ||
    timeoutMinutes > meta.timeoutMinutes.max;

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

  if (payload.selectedDatasetIds.length === 0) {
    errors.push("请至少选择一个评测项。");
  }

  const validDatasetIdSet = new Set(validDatasetIds);
  const hasInvalidDataset = payload.selectedDatasetIds.some(
    (item) => !validDatasetIdSet.has(item),
  );

  if (hasInvalidDataset) {
    errors.push("已选择的评测项里包含失效项，请刷新后重试。");
  }

  return {
    valid: errors.length === 0,
    errors,
  };
};
