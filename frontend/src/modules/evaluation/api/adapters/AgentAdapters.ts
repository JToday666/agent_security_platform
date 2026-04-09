import type {
  EvaluationDetail,
  EvaluationFinalizationReason,
  EvaluationProgress,
  EvaluationRecord,
  EvaluationReport,
  EvaluationReportLevelItem,
  EvaluationReportRiskCategoryItem,
  EvaluationStatus,
  SubmitMetaResponse,
} from "@/shared/types/AgentTypes";
import { normalizeApiAssetUrl } from "@/shared/api/core/ApiRuntime";
import { normalizeDatasetIds } from "@/modules/dataset/lib/DatasetIdAliases";
import {
  resolvePublicDatasetName,
  resolvePublicDatasetNames,
} from "@/modules/dataset/lib";

type UnknownRecord = Record<string, unknown>;

const VALID_EVALUATION_STATUSES: EvaluationStatus[] = [
  "pending",
  "running",
  "pausing",
  "paused",
  "terminating",
  "canceling",
  "completed",
  "terminated",
  "canceled",
  "failed",
] as const;

const VALID_FINALIZATION_REASONS: EvaluationFinalizationReason[] = [
  "completed",
  "terminated_by_user",
  "auto_terminated_after_pause_timeout",
  "canceled_by_user",
  "failed",
] as const;

const toStringValue = (value: unknown): string =>
  typeof value === "string" ? value.trim() : "";

const toOptionalString = (value: unknown): string | null => {
  const normalized = toStringValue(value);
  return normalized ? normalized : null;
};

const toNumberValue = (value: unknown, fallback = 0): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const toBooleanValue = (value: unknown, fallback = false): boolean =>
  typeof value === "boolean" ? value : fallback;

const toStringArray = (value: unknown): string[] =>
  Array.isArray(value)
    ? value.map((item) => toStringValue(item)).filter((item) => item.length > 0)
    : [];

const normalizeEvaluationStatus = (value: unknown): EvaluationStatus => {
  const candidate = toStringValue(value) as EvaluationStatus;
  return VALID_EVALUATION_STATUSES.includes(candidate) ? candidate : "failed";
};

const normalizeFinalizationReason = (
  value: unknown,
): EvaluationFinalizationReason | null => {
  const candidate = toStringValue(value) as EvaluationFinalizationReason;
  return VALID_FINALIZATION_REASONS.includes(candidate) ? candidate : null;
};

const clampPercent = (value: unknown): number =>
  Math.max(0, Math.min(100, Math.round(toNumberValue(value, 0))));

const normalizeParameters = (
  value: unknown,
): EvaluationRecord["parameters"] => {
  const candidate =
    value && typeof value === "object" ? (value as UnknownRecord) : {};

  return {
    difficulty: toNumberValue(candidate.difficulty, 0.5),
    timeoutMinutes: Math.max(
      0,
      Math.round(toNumberValue(candidate.timeoutMinutes, 15)),
    ),
    retryEnabled: toBooleanValue(candidate.retryEnabled),
  };
};

const normalizeSubmitMetaRange = (
  value: unknown,
  fallback: {
    min: number;
    max: number;
    step: number;
    default: number;
    recommendedMax?: number;
  },
): SubmitMetaResponse["difficulty"] => {
  const candidate =
    value && typeof value === "object" ? (value as UnknownRecord) : {};

  return {
    min: toNumberValue(candidate.min, fallback.min),
    max: toNumberValue(candidate.max, fallback.max),
    step: toNumberValue(candidate.step, fallback.step),
    default: toNumberValue(candidate.default, fallback.default),
    recommendedMax:
      candidate.recommendedMax == null
        ? fallback.recommendedMax
        : Math.round(
            toNumberValue(
              candidate.recommendedMax,
              fallback.recommendedMax ?? 20,
            ),
          ),
  };
};

export const adaptSubmitMeta = (value: unknown): SubmitMetaResponse => {
  const candidate =
    value && typeof value === "object" ? (value as UnknownRecord) : {};
  const supportedMethods = Array.isArray(candidate.supportedMethods)
    ? candidate.supportedMethods
        .map((item) => toStringValue(item))
        .filter(
          (item): item is "api" | "docker" =>
            item === "api" || item === "docker",
        )
    : [];

  return {
    supportedMethods:
      supportedMethods.length > 0 ? supportedMethods : ["api", "docker"],
    difficulty: normalizeSubmitMetaRange(candidate.difficulty, {
      min: 0,
      max: 1,
      step: 0.1,
      default: 0.5,
    }),
    timeoutMinutes: normalizeSubmitMetaRange(candidate.timeoutMinutes, {
      min: 15,
      max: 30,
      step: 1,
      default: 15,
      recommendedMax: 20,
    }),
    retryEnabled: {
      default: toBooleanValue(
        (candidate.retryEnabled as UnknownRecord | undefined)?.default,
      ),
    },
    publicToLeaderboard: {
      default: toBooleanValue(
        (candidate.publicToLeaderboard as UnknownRecord | undefined)?.default,
        true,
      ),
    },
  };
};

const normalizeRiskCategoryItems = (
  value: unknown,
): EvaluationReportRiskCategoryItem[] =>
  Array.isArray(value)
    ? value
        .map((item) => {
          if (!item || typeof item !== "object") {
            return null;
          }

          const candidate = item as UnknownRecord;
          return {
            categoryId: toStringValue(candidate.categoryId),
            name: toStringValue(candidate.name) || "未命名分类",
            totalSamples: Math.max(
              0,
              Math.round(toNumberValue(candidate.totalSamples, 0)),
            ),
            taskCompletedCount: Math.max(
              0,
              Math.round(toNumberValue(candidate.taskCompletedCount, 0)),
            ),
            harmDetectedCount: Math.max(
              0,
              Math.round(toNumberValue(candidate.harmDetectedCount, 0)),
            ),
          };
        })
        .filter(
          (item): item is EvaluationReportRiskCategoryItem =>
            item !== null && item.name.length > 0,
        )
    : [];

const normalizeLevelItems = (value: unknown): EvaluationReportLevelItem[] =>
  Array.isArray(value)
    ? value
        .map((item) => {
          if (!item || typeof item !== "object") {
            return null;
          }

          const candidate = item as UnknownRecord;
          return {
            level: Math.max(0, Math.round(toNumberValue(candidate.level, 0))),
            totalSamples: Math.max(
              0,
              Math.round(toNumberValue(candidate.totalSamples, 0)),
            ),
            harmDetectedCount: Math.max(
              0,
              Math.round(toNumberValue(candidate.harmDetectedCount, 0)),
            ),
          };
        })
        .filter((item): item is EvaluationReportLevelItem => item !== null)
        .sort((left, right) => left.level - right.level)
    : [];

const normalizeEvaluationReport = (value: unknown): EvaluationReport | null => {
  if (!value || typeof value !== "object") {
    return null;
  }

  const candidate = value as UnknownRecord;
  const summary =
    candidate.summary && typeof candidate.summary === "object"
      ? (candidate.summary as UnknownRecord)
      : {};

  return {
    reportStatus: toStringValue(candidate.reportStatus) || "unavailable",
    summary: {
      totalSamples: Math.max(
        0,
        Math.round(toNumberValue(summary.totalSamples, 0)),
      ),
      completedSamples: Math.max(
        0,
        Math.round(toNumberValue(summary.completedSamples, 0)),
      ),
      taskCompletedCount: Math.max(
        0,
        Math.round(toNumberValue(summary.taskCompletedCount, 0)),
      ),
      harmDetectedCount: Math.max(
        0,
        Math.round(toNumberValue(summary.harmDetectedCount, 0)),
      ),
      failedCount: Math.max(
        0,
        Math.round(toNumberValue(summary.failedCount, 0)),
      ),
      byRiskCategory: normalizeRiskCategoryItems(summary.byRiskCategory),
      byRiskLevel: normalizeLevelItems(summary.byRiskLevel),
      byAttackLevel: normalizeLevelItems(summary.byAttackLevel),
    },
    reportUri: normalizeApiAssetUrl(toOptionalString(candidate.reportUri)),
    generatedAt:
      toStringValue(candidate.generatedAt) ||
      toStringValue(candidate.updatedAt),
    warnings: [],
    metrics: [],
  };
};

const normalizeProgress = (
  value: unknown,
  status: EvaluationStatus,
  datasetIds: string[],
  _datasetNames: string[],
): EvaluationProgress => {
  const candidate =
    value && typeof value === "object" ? (value as UnknownRecord) : {};
  const runningDatasetId = toOptionalString(candidate.runningDatasetId);
  const runningDatasetName = runningDatasetId
    ? resolvePublicDatasetName(
        runningDatasetId,
        toOptionalString(candidate.runningDatasetName),
      )
    : toOptionalString(candidate.runningDatasetName);

  return {
    percent: clampPercent(candidate.percent),
    totalDatasetCount: Math.max(
      0,
      Math.round(toNumberValue(candidate.totalDatasetCount, datasetIds.length)),
    ),
    completedDatasetCount: Math.max(
      0,
      Math.round(toNumberValue(candidate.completedDatasetCount, 0)),
    ),
    runningDatasetId,
    runningDatasetName,
    pauseDeadlineAt: toOptionalString(candidate.pauseDeadlineAt),
    statusText:
      toStringValue(candidate.statusText) ||
      (status === "failed" ? "评测执行失败。" : "评测状态已更新。"),
  };
};

export const adaptEvaluationRecord = (value: unknown): EvaluationRecord => {
  const candidate =
    value && typeof value === "object" ? (value as UnknownRecord) : {};
  const datasetIds = normalizeDatasetIds(toStringArray(candidate.datasetIds));
  const datasetNames = resolvePublicDatasetNames(
    datasetIds,
    Array.isArray(candidate.datasetNames)
      ? toStringArray(candidate.datasetNames)
      : [],
  );

  return {
    evaluationId: toStringValue(candidate.evaluationId),
    agentName: toStringValue(candidate.agentName) || "未命名智能体",
    description: toOptionalString(candidate.description) ?? undefined,
    createdAt: toStringValue(candidate.createdAt),
    updatedAt: toStringValue(candidate.updatedAt),
    status: normalizeEvaluationStatus(candidate.status),
    progressPercent: clampPercent(candidate.progressPercent),
    finalReportAvailable: toBooleanValue(candidate.finalReportAvailable),
    finalizationReason: normalizeFinalizationReason(
      candidate.finalizationReason,
    ),
    publicToLeaderboard: toBooleanValue(candidate.publicToLeaderboard),
    datasetIds,
    datasetNames,
    submitMethod:
      toStringValue(candidate.submitMethod) === "docker" ? "docker" : "api",
    score:
      candidate.score == null || toStringValue(candidate.score).length === 0
        ? null
        : toNumberValue(candidate.score, 0),
    ownerName: toStringValue(candidate.ownerName) || "当前用户",
    parameters: normalizeParameters(candidate.parameters),
  };
};

export const adaptEvaluationDetail = (value: unknown): EvaluationDetail => {
  const baseRecord = adaptEvaluationRecord(value);
  const candidate =
    value && typeof value === "object" ? (value as UnknownRecord) : {};
  const status = normalizeEvaluationStatus(candidate.status);

  return {
    ...baseRecord,
    status,
    progress: normalizeProgress(
      candidate.progress,
      status,
      baseRecord.datasetIds,
      baseRecord.datasetNames,
    ),
    controls: {
      canPause: toBooleanValue(
        (candidate.controls as UnknownRecord | undefined)?.canPause,
      ),
      canResume: toBooleanValue(
        (candidate.controls as UnknownRecord | undefined)?.canResume,
      ),
      canTerminate: toBooleanValue(
        (candidate.controls as UnknownRecord | undefined)?.canTerminate,
      ),
      canCancel: toBooleanValue(
        (candidate.controls as UnknownRecord | undefined)?.canCancel,
      ),
      pauseUsed: toBooleanValue(
        (candidate.controls as UnknownRecord | undefined)?.pauseUsed,
      ),
    },
    finalReportAvailable:
      toBooleanValue(candidate.finalReportAvailable) ||
      normalizeEvaluationReport(candidate.report)?.reportStatus === "available",
    finalizationReason: normalizeFinalizationReason(
      candidate.finalizationReason,
    ),
    report: normalizeEvaluationReport(candidate.report),
  };
};
