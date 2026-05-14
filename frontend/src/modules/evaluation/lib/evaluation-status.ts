import type {
  EvaluationFinalizationReason,
  EvaluationStatus,
} from "@/shared/types/agent-types";
import {
  type AppTranslator,
  translateRuntimeMessage,
} from "@/app/i18n/runtime-translator";
import { hasAvailableEvaluationActions } from "@/modules/evaluation/model/evaluation-controls";
import type { AppIconName } from "@/shared/ui/branding/app-icon-registry";

export type EvaluationStatusTone =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "terminated"
  | "canceled"
  | "failed";

export type EvaluationStatusTagTone =
  | "brand"
  | "info"
  | "success"
  | "warning"
  | "danger";

export interface EvaluationStatusMetadata {
  status: EvaluationStatus;
  labelKey: `evaluation.status.${EvaluationStatus}`;
  tone: EvaluationStatusTone;
  tagTone: EvaluationStatusTagTone;
  icon: AppIconName;
  pollable: boolean;
}

export const EVALUATION_STATUS_METADATA = [
  {
    status: "queued",
    labelKey: "evaluation.status.queued",
    tone: "pending",
    tagTone: "warning",
    icon: "app:status.queued",
    pollable: true,
  },
  {
    status: "pending",
    labelKey: "evaluation.status.pending",
    tone: "pending",
    tagTone: "warning",
    icon: "app:status.pending",
    pollable: true,
  },
  {
    status: "running",
    labelKey: "evaluation.status.running",
    tone: "running",
    tagTone: "info",
    icon: "app:status.running",
    pollable: true,
  },
  {
    status: "pausing",
    labelKey: "evaluation.status.pausing",
    tone: "pending",
    tagTone: "warning",
    icon: "app:status.paused",
    pollable: true,
  },
  {
    status: "paused",
    labelKey: "evaluation.status.paused",
    tone: "paused",
    tagTone: "warning",
    icon: "app:status.paused",
    pollable: false,
  },
  {
    status: "terminating",
    labelKey: "evaluation.status.terminating",
    tone: "pending",
    tagTone: "warning",
    icon: "app:status.terminated",
    pollable: true,
  },
  {
    status: "canceling",
    labelKey: "evaluation.status.canceling",
    tone: "running",
    tagTone: "info",
    icon: "app:status.canceled",
    pollable: true,
  },
  {
    status: "completed",
    labelKey: "evaluation.status.completed",
    tone: "completed",
    tagTone: "success",
    icon: "app:status.completed",
    pollable: false,
  },
  {
    status: "terminated",
    labelKey: "evaluation.status.terminated",
    tone: "terminated",
    tagTone: "brand",
    icon: "app:status.terminated",
    pollable: false,
  },
  {
    status: "canceled",
    labelKey: "evaluation.status.canceled",
    tone: "canceled",
    tagTone: "danger",
    icon: "app:status.canceled",
    pollable: false,
  },
  {
    status: "failed",
    labelKey: "evaluation.status.failed",
    tone: "failed",
    tagTone: "danger",
    icon: "app:status.failed",
    pollable: false,
  },
] as const satisfies readonly EvaluationStatusMetadata[];

export const EVALUATION_STATUS_OPTIONS = EVALUATION_STATUS_METADATA.map(
  (item) => item.status,
);

const evaluationStatusMetadataByStatus = new Map<
  EvaluationStatus,
  EvaluationStatusMetadata
>(EVALUATION_STATUS_METADATA.map((item) => [item.status, item]));

export const getEvaluationStatusMetadata = (
  status: EvaluationStatus,
): EvaluationStatusMetadata => evaluationStatusMetadataByStatus.get(status)!;

export const getEvaluationStatusLabel = (
  status: EvaluationStatus,
  t: AppTranslator = translateRuntimeMessage,
): string => t(getEvaluationStatusMetadata(status).labelKey);

export const getEvaluationStatusIcon = (
  status: EvaluationStatus,
): AppIconName => getEvaluationStatusMetadata(status).icon;

export const getEvaluationStatusTagTone = (
  status: EvaluationStatus,
): EvaluationStatusTagTone => getEvaluationStatusMetadata(status).tagTone;

export const getEvaluationStatusFilterOptions = (
  t: AppTranslator = translateRuntimeMessage,
): Array<{ label: string; value: EvaluationStatus }> =>
  EVALUATION_STATUS_METADATA.map((item) => ({
    label: t(item.labelKey),
    value: item.status,
  }));

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

export const getEvaluationStatusTone = (
  status: EvaluationStatus,
): EvaluationStatusTone => getEvaluationStatusMetadata(status).tone;

export const shouldPollEvaluation = (status: EvaluationStatus): boolean =>
  getEvaluationStatusMetadata(status).pollable;

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
