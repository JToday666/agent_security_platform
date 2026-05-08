import type {
  EvaluationDetail,
  EvaluationFinalizationReason,
  EvaluationProgress,
  EvaluationRecord,
  EvaluationReport,
  EvaluationReportPayload,
  EvaluationStatus,
} from "@/shared/types/agent-types";
import {
  resolvePublicDatasetName,
  resolvePublicDatasetNames,
} from "@/modules/dataset/lib/dataset-display-utils";
import type {
  ResolvedEvaluationState,
  StoredEvaluationRecord,
} from "./evaluation-service-shared";
import {
  clampPercent,
  getDatasetCount,
  MOCK_DATASET_DURATION_MS,
  MOCK_PENDING_DELAY_MS,
} from "./evaluation-service-shared";
import { buildEvaluationControls } from "@/modules/evaluation/model/evaluation-controls";

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

const buildSampleSummary = (score: number | null, totalSamples: number) => {
  if (score === null || totalSamples <= 0) {
    return null;
  }

  const riskCount = Math.max(0, Math.round(((100 - score) / 100) * totalSamples));
  const error = Math.max(0, Math.round(riskCount * 0.22));
  const failed = Math.max(0, riskCount - error);

  return {
    total: totalSamples,
    success: Math.max(0, totalSamples - failed - error),
    failed,
    error,
  };
};

const buildRepresentativeSamples = (
  evaluationId: string,
  datasetNames: string[],
  sampleSummary: NonNullable<ReturnType<typeof buildSampleSummary>> | null,
) => {
  const datasetName = datasetNames[0] ?? "未命名数据集";
  const replayBase =
    "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4";

  return {
    success:
      sampleSummary && sampleSummary.success > 0
        ? {
            sampleId: `${evaluationId}_success_001`,
            datasetName,
            normalizedResult: "success" as const,
            outcomeReasonText: "样本安全完成。",
            replayUrl: replayBase,
          }
        : null,
    failed:
      sampleSummary && sampleSummary.failed > 0
        ? {
            sampleId: `${evaluationId}_failed_001`,
            datasetName,
            normalizedResult: "failed" as const,
            outcomeReasonText: "Oracle 判定存在不安全行为。",
            replayUrl: replayBase,
          }
        : null,
    error:
      sampleSummary && sampleSummary.error > 0
        ? {
            sampleId: `${evaluationId}_error_001`,
            datasetName,
            normalizedResult: "error" as const,
            outcomeReasonText: "样本执行异常。",
            replayUrl: replayBase,
          }
        : null,
  };
};

export const buildMockReportPayload = (
  state: Pick<
    ResolvedEvaluationState,
    | "evaluationId"
    | "agentName"
    | "createdAt"
    | "updatedAt"
    | "datasetIds"
    | "datasetNames"
    | "score"
    | "parameters"
    | "finalReportAvailable"
  >,
): EvaluationReportPayload | null => {
  if (!state.finalReportAvailable || typeof state.score !== "number") {
    return null;
  }

  const datasetCount = Math.max(1, state.datasetIds.length);
  const totalSamples = datasetCount * 20;
  const sampleSummary = buildSampleSummary(state.score, totalSamples) ?? {
    total: totalSamples,
    success: totalSamples,
    failed: 0,
    error: 0,
  };
  const conservativeScore = Number(state.score.toFixed(1));
  const performanceScore = Number(Math.min(99, state.score + 3.7).toFixed(1));
  const hardScore = Number(Math.max(0, state.score - 11.8).toFixed(1));
  const unsafeRate = Number(((sampleSummary.failed / sampleSummary.total) * 100).toFixed(1));
  const completionRate =
    sampleSummary.total === 0
      ? 0
      : Number(
          (
            (sampleSummary.success + sampleSummary.failed) /
            sampleSummary.total
          ).toFixed(4),
        );
  const successRate =
    sampleSummary.total === 0
      ? 0
      : Number((sampleSummary.success / sampleSummary.total).toFixed(4));

  return {
    evaluationId: state.evaluationId,
    status: "ready",
    generatedAt: state.updatedAt,
    scores: {
      conservativeScore,
      performanceScore,
      confidence: Number(Math.min(96, 70 + datasetCount * 3.4).toFixed(1)),
      completionScore: Number((completionRate * 100).toFixed(1)),
      safetyScore: Number(Math.max(0, 100 - unsafeRate * 1.6).toFixed(1)),
      hardScore,
      unsafeRate,
      timeScore: Number(
        Math.max(52, 88 - state.parameters.timeoutMinutes * 0.8).toFixed(1),
      ),
    },
    rawStats: {
      ...sampleSummary,
      completionRate,
      successRate,
      conditionalSuccessRate:
        sampleSummary.success + sampleSummary.failed === 0
          ? 0
          : Number(
              (
                sampleSummary.success /
                (sampleSummary.success + sampleSummary.failed)
              ).toFixed(4),
            ),
    },
    posteriorInterval: {
      psQ05: Number(Math.max(0, conservativeScore - 5.4).toFixed(1)),
      psQ50: conservativeScore,
      psQ95: Number(Math.min(100, conservativeScore + 4.8).toFixed(1)),
    },
    coverage: {
      difficultyBucketHitCount: 5,
      difficultyCoverageRatio: 1,
    },
    breakdowns: {
      outcomeSummary: sampleSummary,
      difficultyBuckets: ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"].map(
        (bucket, index) => {
          const total = Math.max(1, Math.round(totalSamples / 5));
          const difficultyPenalty = index * 0.07;
          const success = Math.max(
            0,
            Math.round(total * Math.max(0.18, successRate - difficultyPenalty)),
          );
          const error = Math.max(0, Math.round((total - success) * 0.25));
          const failed = Math.max(0, total - success - error);
          return {
            bucket,
            total,
            success,
            failed,
            error,
            successRate: total === 0 ? 0 : Number((success / total).toFixed(4)),
          };
        },
      ),
      datasetSummaries: state.datasetIds.map((datasetId, index) => {
        const total = 20;
        const localScore = Math.max(48, conservativeScore - index * 3);
        const failed = Math.max(0, Math.round(((100 - localScore) / 100) * total * 0.68));
        const error = Math.max(0, Math.round(((100 - localScore) / 100) * total * 0.18));
        return {
          datasetId,
          datasetName: state.datasetNames[index] ?? datasetId,
          total,
          success: Math.max(0, total - failed - error),
          failed,
          error,
        };
      }),
      sampleScatterPoints: Array.from({ length: Math.min(totalSamples, 80) }, (_, index) => {
        const difficulty = Number(((index % 20) / 20 + 0.03).toFixed(2));
        const durationMs = 11000 + index * 390 + Math.round(difficulty * 9000);
        const riskBand = index % 11;
        return {
          sampleId: `${state.evaluationId}_sample_${String(index + 1).padStart(3, "0")}`,
          difficulty,
          durationMs,
          normalizedResult:
            riskBand === 0
              ? ("error" as const)
              : riskBand <= 2
                ? ("failed" as const)
                : ("success" as const),
        };
      }),
    },
    versions: {
      difficultyVersion: "dv_2026q2_v1",
      scoreModelVersion: "score_v1",
      benchmarkVersion: "bm_v1",
    },
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
    case "queued":
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
  const totalDatasetCount = getDatasetCount(record);
  const sampleSummary = buildSampleSummary(record.score, totalDatasetCount * 20);

  return {
    evaluationId: record.evaluationId,
    agentName: record.agentName,
    description: record.description,
    createdAt: record.createdAt,
    updatedAt: record.updatedAt,
    status: record.status,
    publicToLeaderboard: record.publicToLeaderboard,
    leaderboardDisplayMode: record.leaderboardDisplayMode,
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
    sampleSummary,
    representativeSamples: buildRepresentativeSamples(
      record.evaluationId,
      resolvePublicDatasetNames(record.datasetIds, record.datasetNames),
      sampleSummary,
    ),
    downloads: {
      sampleDetailsUrl: `/api/v1/evaluations/${record.evaluationId}/samples/export`,
    },
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
  const sampleSummary = buildSampleSummary(record.score, record.datasetIds.length * 20);

  return {
    evaluationId: record.evaluationId,
    agentName: record.agentName,
    description: record.description,
    createdAt: record.createdAt,
    updatedAt: record.updatedAt,
    status: record.status,
    publicToLeaderboard: record.publicToLeaderboard,
    leaderboardDisplayMode: record.leaderboardDisplayMode,
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
    sampleSummary,
    representativeSamples: buildRepresentativeSamples(
      record.evaluationId,
      resolvePublicDatasetNames(record.datasetIds, record.datasetNames),
      sampleSummary,
    ),
    downloads: {
      sampleDetailsUrl: `/api/v1/evaluations/${record.evaluationId}/samples/export`,
    },
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
