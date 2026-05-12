import {
  translateRuntimeMessage,
  type AppTranslator,
} from "@/app/i18n/runtime-translator";
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
  t: AppTranslator = translateRuntimeMessage,
): string => {
  const leaderboardDisplayLabel =
    payload.leaderboardDisplayMode === "anonymous"
      ? t("submission.leaderboardDisplay.anonymous.title")
      : t("submission.leaderboardDisplay.public.title");
  const header = [
    t("submission.confirm.agentName", {
      agentName: agentName || t("submission.summary.notSelected"),
    }),
    t("submission.confirm.submitMethod", {
      method: payload.submitMethod.toUpperCase(),
    }),
    t("submission.confirm.datasetCount", {
      count: payload.selectedDatasetIds.length,
    }),
    t("submission.confirm.leaderboardDisplay", {
      mode: leaderboardDisplayLabel,
    }),
  ].join("\n");

  if (!warnings.length) {
    return t("submission.confirm.successMessage", { summary: header });
  }

  return t("submission.confirm.warningMessage", {
    summary: header,
    warnings: warnings.join("\n- "),
  });
};
