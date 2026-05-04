import type { SubmitAgentPayload } from "@/shared/types/agent-types";

export const buildSubmitRequestId = (): string => {
  if (
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
  ) {
    return `submit_${crypto.randomUUID()}`;
  }

  return `submit_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
};

export const isSubmitAbortError = (error: unknown): boolean =>
  error instanceof DOMException
    ? error.name === "AbortError"
    : error instanceof Error
      ? error.name === "AbortError" || error.name === "CanceledError"
      : false;

export const buildSubmitConfirmMessage = (
  agentName: string,
  warnings: string[],
  payload: SubmitAgentPayload,
): string => {
  const header = [
    `智能体名称：${agentName || "未选择"}`,
    `提交方式：${payload.submitMethod.toUpperCase()}`,
    `数据集数量：${payload.selectedDatasetIds.length}`,
  ].join("\n");

  if (!warnings.length) {
    return `${header}\n\n检查已通过，确认后将创建评测任务。`;
  }

  return `${header}\n\n请先确认以下提示：\n- ${warnings.join(
    "\n- ",
  )}\n\n确认后将创建评测任务。`;
};
