import type {
  EvaluationDetail,
  EvaluationFinalizationReason,
  EvaluationProgress,
  EvaluationRecord,
  EvaluationReport,
  EvaluationStatus,
} from "@/shared/types/AgentTypes";
import {
  resolvePublicDatasetName,
  resolvePublicDatasetNames,
} from "@/modules/dataset/lib";
import type {
  ResolvedEvaluationState,
  StoredEvaluationRecord,
} from "./EvaluationServiceShared.ts";
import {
  clampPercent,
  getDatasetCount,
  MOCK_DATASET_DURATION_MS,
  MOCK_PENDING_DELAY_MS,
} from "./EvaluationServiceShared.ts";
import { buildEvaluationControls } from "@/modules/evaluation/model/EvaluationControls";

const escapeRegex = (value: string): string =>
  value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const sanitizeStatusText = (
  statusText: string,
  datasetId: string | null,
  datasetName: string | null,
): string => {
  if (!statusText || !datasetId || !datasetName || datasetId === datasetName) {
    return statusText;
  }

  const escapedDatasetId = escapeRegex(datasetId);
  const escapedDatasetName = escapeRegex(datasetName);
  const pairedPatterns = [
    new RegExp(`${escapedDatasetId}（${escapedDatasetName}）`, "g"),
    new RegExp(`${escapedDatasetId}\\(${escapedDatasetName}\\)`, "g"),
  ];

  const sanitized = pairedPatterns.reduce(
    (currentText, pattern) => currentText.replace(pattern, datasetName),
    statusText,
  );

  return sanitized.replace(new RegExp(escapedDatasetId, "g"), datasetName);
};

export const sanitizeEvaluationRecord = (
  record: EvaluationRecord,
): EvaluationRecord => ({
  ...record,
  datasetNames: resolvePublicDatasetNames(
    record.datasetIds,
    record.datasetNames,
  ),
});

export const sanitizeEvaluationDetail = (
  detail: EvaluationDetail,
): EvaluationDetail => {
  const datasetNames = resolvePublicDatasetNames(
    detail.datasetIds,
    detail.datasetNames,
  );
  const runningDatasetName = detail.progress.runningDatasetId
    ? resolvePublicDatasetName(
        detail.progress.runningDatasetId,
        detail.progress.runningDatasetName,
      )
    : detail.progress.runningDatasetName;

  return {
    ...detail,
    datasetNames,
    progress: {
      ...detail.progress,
      runningDatasetName,
      statusText: sanitizeStatusText(
        detail.progress.statusText,
        detail.progress.runningDatasetId,
        runningDatasetName,
      ),
    },
  };
};

const buildReport = (record: {
  finalReportAvailable: boolean;
  reportGeneratedAt: string | null;
  score: number | null;
  completedDatasetCount: number;
  datasetIds: string[];
}): EvaluationReport | null => {
  if (!record.finalReportAvailable || record.score === null) {
    return null;
  }

  const totalDatasetCount = getDatasetCount(record);
  const completedDatasetCount = Math.min(
    record.completedDatasetCount,
    totalDatasetCount,
  );
  const safeScore = record.score;

  return {
    reportStatus: "available",
    summary: {
      totalSamples: totalDatasetCount * 120,
      completedSamples: completedDatasetCount * 120,
      taskCompletedCount: completedDatasetCount,
      harmDetectedCount: Math.max(
        0,
        Math.round((100 - safeScore) * completedDatasetCount),
      ),
      failedCount: Math.max(0, totalDatasetCount - completedDatasetCount),
      byRiskCategory: record.datasetIds.map((datasetId, index) => ({
        categoryId: datasetId,
        name: resolvePublicDatasetName(datasetId),
        totalSamples: 120,
        taskCompletedCount: index < completedDatasetCount ? 1 : 0,
        harmDetectedCount:
          index < completedDatasetCount
            ? Math.max(0, Math.round((100 - safeScore) / 8))
            : 0,
      })),
      byRiskLevel: [1, 2, 3].map((level) => ({
        level,
        totalSamples: totalDatasetCount * 40,
        harmDetectedCount: Math.max(
          0,
          Math.round(((4 - level) * (100 - safeScore)) / 6),
        ),
      })),
      byAttackLevel: [1, 2, 3].map((level) => ({
        level,
        totalSamples: totalDatasetCount * 40,
        harmDetectedCount: Math.max(
          0,
          Math.round((level * (100 - safeScore)) / 7),
        ),
      })),
    },
    reportUri: null,
    generatedAt: record.reportGeneratedAt ?? new Date().toISOString(),
    warnings: [],
    metrics: [],
  };
};

const buildStatusText = (
  status: EvaluationStatus,
  progress: Pick<
    EvaluationProgress,
    | "runningDatasetName"
    | "completedDatasetCount"
    | "totalDatasetCount"
    | "pauseDeadlineAt"
  >,
  reason: EvaluationFinalizationReason | null,
): string => {
  switch (status) {
    case "pending":
      return "任务已创建，正在等待调度。";
    case "running":
      return progress.runningDatasetName
        ? `当前正在评测数据集 ${progress.runningDatasetName}。`
        : "任务正在执行中。";
    case "pausing":
      return progress.runningDatasetName
        ? `已收到暂停请求，当前数据集 ${progress.runningDatasetName} 完成后将暂停。`
        : "已收到暂停请求，当前任务即将暂停。";
    case "paused":
      return progress.pauseDeadlineAt
        ? `任务已暂停，请在 ${progress.pauseDeadlineAt} 前选择继续、终止或取消。`
        : "任务已暂停。";
    case "terminating":
      return progress.runningDatasetName
        ? `已收到终止请求，当前数据集 ${progress.runningDatasetName} 完成后将结束任务。`
        : "已收到终止请求，当前任务即将结束。";
    case "canceling":
      return "正在取消任务并中断执行。";
    case "completed":
      return "所有数据集已评测完成，已生成最终报告。";
    case "terminated":
      return reason === "auto_terminated_after_pause_timeout"
        ? "任务在暂停超时后自动终止，已生成最终报告。"
        : `任务已结束，已完成 ${progress.completedDatasetCount}/${progress.totalDatasetCount} 个数据集并生成最终报告。`;
    case "canceled":
      return "任务已取消，未生成最终报告。";
    case "failed":
      return "任务执行失败，请稍后重试。";
  }
};

const buildProgress = (
  record: StoredEvaluationRecord,
  status: EvaluationStatus,
  now: number,
): EvaluationProgress => {
  const totalDatasetCount = getDatasetCount(record);
  const completedDatasetCount = Math.min(
    record.completedDatasetCount,
    totalDatasetCount,
  );
  const phaseElapsed = Math.max(
    0,
    now - new Date(record.phaseStartedAt).getTime(),
  );
  const runningDatasetId =
    status === "running" || status === "pausing" || status === "terminating"
      ? (record.datasetIds[completedDatasetCount] ?? null)
      : null;
  const runningDatasetName = runningDatasetId
    ? resolvePublicDatasetName(
        runningDatasetId,
        record.datasetNames[completedDatasetCount],
      )
    : null;

  let percent = Math.round((completedDatasetCount / totalDatasetCount) * 100);
  if (status === "pending") {
    percent = clampPercent((phaseElapsed / MOCK_PENDING_DELAY_MS) * 8);
  } else if (
    status === "running" ||
    status === "pausing" ||
    status === "terminating"
  ) {
    const partial = Math.min(phaseElapsed / MOCK_DATASET_DURATION_MS, 0.98);
    percent = clampPercent(
      ((completedDatasetCount + partial) / totalDatasetCount) * 100,
    );
  } else if (status === "completed") {
    percent = 100;
  } else if (status === "canceled" || status === "failed") {
    percent = clampPercent((completedDatasetCount / totalDatasetCount) * 100);
  }

  const progressBase = {
    percent,
    totalDatasetCount,
    completedDatasetCount,
    runningDatasetId,
    runningDatasetName,
    pauseDeadlineAt: status === "paused" ? record.pauseDeadlineAt : null,
  };

  return {
    ...progressBase,
    statusText: buildStatusText(
      status,
      progressBase,
      record.finalizationReason,
    ),
  };
};

export const buildResolvedStateFromStored = (
  record: StoredEvaluationRecord,
  now = Date.now(),
): ResolvedEvaluationState => {
  const progress = buildProgress(record, record.status, now);
  const controls = buildEvaluationControls(record.status, record.pauseUsed);
  const report = buildReport(record);

  return {
    evaluationId: record.evaluationId,
    agentName: record.agentName,
    description: record.description,
    createdAt: record.createdAt,
    updatedAt: record.updatedAt,
    status: record.status,
    publicToLeaderboard: record.publicToLeaderboard,
    datasetIds: record.datasetIds,
    datasetNames: resolvePublicDatasetNames(
      record.datasetIds,
      record.datasetNames,
    ),
    submitMethod: record.submitMethod,
    score: record.score,
    ownerName: record.ownerName,
    parameters: record.parameters,
    progressPercent: progress.percent,
    finalReportAvailable: record.finalReportAvailable,
    finalizationReason: record.finalizationReason,
    progress,
    controls,
    report,
  };
};

export const buildResolvedStateFromReference = (
  record: EvaluationRecord,
): ResolvedEvaluationState => {
  const progress: EvaluationProgress = {
    percent: record.progressPercent,
    totalDatasetCount: record.datasetIds.length,
    completedDatasetCount: record.datasetIds.length,
    runningDatasetId: null,
    runningDatasetName: null,
    pauseDeadlineAt: null,
    statusText: "所有数据集已评测完成，已生成最终报告。",
  };

  const safeScore = record.score ?? 0;

  return {
    evaluationId: record.evaluationId,
    agentName: record.agentName,
    description: record.description,
    createdAt: record.createdAt,
    updatedAt: record.updatedAt,
    status: record.status,
    publicToLeaderboard: record.publicToLeaderboard,
    datasetIds: record.datasetIds,
    datasetNames: resolvePublicDatasetNames(
      record.datasetIds,
      record.datasetNames,
    ),
    submitMethod: record.submitMethod,
    score: record.score,
    ownerName: record.ownerName,
    parameters: record.parameters,
    progressPercent: record.progressPercent,
    finalReportAvailable: record.finalReportAvailable,
    finalizationReason: record.finalizationReason,
    progress,
    controls: buildEvaluationControls(record.status, false),
    report:
      record.finalReportAvailable && typeof record.score === "number"
        ? {
            reportStatus: "available",
            summary: {
              totalSamples: record.datasetIds.length * 120,
              completedSamples: record.datasetIds.length * 120,
              taskCompletedCount: record.datasetIds.length,
              harmDetectedCount: Math.max(
                0,
                Math.round((100 - safeScore) * record.datasetIds.length),
              ),
              failedCount: 0,
              byRiskCategory: record.datasetIds.map((datasetId) => ({
                categoryId: datasetId,
                name: resolvePublicDatasetName(datasetId),
                totalSamples: 120,
                taskCompletedCount: 1,
                harmDetectedCount: Math.max(
                  0,
                  Math.round((100 - safeScore) / 8),
                ),
              })),
              byRiskLevel: [1, 2, 3].map((level) => ({
                level,
                totalSamples: record.datasetIds.length * 40,
                harmDetectedCount: Math.max(
                  0,
                  Math.round(((4 - level) * (100 - safeScore)) / 6),
                ),
              })),
              byAttackLevel: [1, 2, 3].map((level) => ({
                level,
                totalSamples: record.datasetIds.length * 40,
                harmDetectedCount: Math.max(
                  0,
                  Math.round((level * (100 - safeScore)) / 7),
                ),
              })),
            },
            reportUri: null,
            generatedAt: record.updatedAt,
            warnings: [],
            metrics: [],
          }
        : null,
  };
};
