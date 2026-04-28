import type {
  EvaluationFinalizationReason,
  EvaluationStatus,
} from "@/shared/types/agent-types";
import { hasAvailableEvaluationActions } from "@/modules/evaluation/model/evaluation-controls";

const TERMINAL_EVALUATION_STATUSES: EvaluationStatus[] = [
  "completed",
  "terminated",
  "canceled",
  "failed",
];

const isTerminalEvaluationStatus = (status: EvaluationStatus): boolean =>
  TERMINAL_EVALUATION_STATUSES.includes(status);

export const getEvaluationStatusLabel = (status: EvaluationStatus): string => {
  switch (status) {
    case "queued":
    case "pending":
      return "排队中";
    case "running":
      return "执行中";
    case "pausing":
      return "暂停中";
    case "paused":
      return "已暂停";
    case "terminating":
      return "终止中";
    case "canceling":
      return "取消中";
    case "completed":
      return "已完成";
    case "terminated":
      return "已终止";
    case "canceled":
      return "已取消";
    case "failed":
      return "已失败";
  }
};

export const getFinalizationReasonLabel = (
  reason: EvaluationFinalizationReason | null,
): string => {
  switch (reason) {
    case "completed":
      return "任务已完成";
    case "terminated_by_user":
      return "用户终止后生成报告";
    case "auto_terminated_after_pause_timeout":
      return "暂停超时后自动终止";
    case "canceled_by_user":
      return "用户取消任务";
    case "failed":
      return "任务执行失败";
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
): string =>
  hasVisibleScore(score, finalReportAvailable) ? `${score} 分` : "待生成";

export const hasAvailableActions = hasAvailableEvaluationActions;
