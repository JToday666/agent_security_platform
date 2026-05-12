import type {
  EvaluationFinalizationReason,
  EvaluationStatus,
} from "@/shared/types/agent-types";
import {
  type AppTranslator,
  translateRuntimeMessage,
} from "@/app/i18n/runtime-translator";
import { hasAvailableEvaluationActions } from "@/modules/evaluation/model/evaluation-controls";

const TERMINAL_EVALUATION_STATUSES: EvaluationStatus[] = [
  "completed",
  "terminated",
  "canceled",
  "failed",
];

const isTerminalEvaluationStatus = (status: EvaluationStatus): boolean =>
  TERMINAL_EVALUATION_STATUSES.includes(status);

export const getEvaluationStatusLabel = (
  status: EvaluationStatus,
  t: AppTranslator = translateRuntimeMessage,
): string => t(`evaluation.status.${status}`);

export const getFinalizationReasonLabel = (
  reason: EvaluationFinalizationReason | null,
  t: AppTranslator = translateRuntimeMessage,
): string => {
  switch (reason) {
    case "completed":
      return t("evaluation.finalization.completed");
    case "terminated_by_user":
      return t("evaluation.finalization.terminatedByUser");
    case "auto_terminated_after_pause_timeout":
      return t("evaluation.finalization.autoTerminatedAfterPauseTimeout");
    case "canceled_by_user":
      return t("evaluation.finalization.canceledByUser");
    case "failed":
      return t("evaluation.finalization.failed");
    default:
      return "";
  }
};

export const getEvaluationStatusTone = (status: EvaluationStatus): string => {
  switch (status) {
    case "queued":
    case "pending":
    case "pausing":
    case "terminating":
      return "pending";
    case "running":
    case "canceling":
      return "running";
    case "paused":
      return "paused";
    case "completed":
      return "completed";
    case "terminated":
      return "terminated";
    case "canceled":
      return "canceled";
    case "failed":
      return "failed";
  }
};

export const shouldPollEvaluation = (status: EvaluationStatus): boolean =>
  status !== "paused" && !isTerminalEvaluationStatus(status);

export const hasVisibleScore = (
  score: number | null,
  finalReportAvailable: boolean,
): boolean => finalReportAvailable && typeof score === "number";

export const formatEvaluationScore = (
  score: number | null,
  finalReportAvailable: boolean,
  t: AppTranslator = translateRuntimeMessage,
): string =>
  hasVisibleScore(score, finalReportAvailable)
    ? t("evaluation.common.score", { score })
    : t("evaluation.summary.scorePending");

export const hasAvailableActions = hasAvailableEvaluationActions;
