import type {
  EvaluationControls,
  EvaluationStatus,
} from "@/shared/types/agent-types";

export const buildEvaluationControls = (
  status: EvaluationStatus,
  pauseUsed: boolean,
): EvaluationControls => ({
  canPause: status === "running" && !pauseUsed,
  canResume: status === "paused",
  canTerminate: status === "running" || status === "paused",
  canCancel:
    status === "pending" || status === "running" || status === "paused",
  pauseUsed,
});

export const hasAvailableEvaluationActions = (
  controls: EvaluationControls,
): boolean =>
  controls.canPause ||
  controls.canResume ||
  controls.canTerminate ||
  controls.canCancel;
