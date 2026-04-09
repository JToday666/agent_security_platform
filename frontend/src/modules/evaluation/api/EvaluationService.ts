import request from "@/shared/api/core/HttpClient";
import { ApiConfig } from "@/shared/api/core/Config";
import { STORAGE_KEYS } from "@/shared/constants/StorageKeys";
import type {
  EvaluationAction,
  EvaluationActionRequest,
  EvaluationControls,
  EvaluationDetail,
  EvaluationFinalizationReason,
  EvaluationMetric,
  EvaluationProgress,
  EvaluationRecord,
  EvaluationReport,
  EvaluationStatus,
  PrecheckResponse,
  SubmitAgentPayload,
  SubmitMetaResponse,
  SubmitResponse,
} from "@/shared/types/AgentTypes";
import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
} from "@/shared/api/core/MockApiUtils";
import { withMemoryCache } from "@/shared/api/core/MemoryCache";
import { buildSubmitAgentApiPayload } from "@/modules/dataset/api/adapters/DatasetAdapters";
import {
  adaptEvaluationDetail,
  adaptEvaluationRecord,
  adaptSubmitMeta,
} from "@/modules/evaluation/api/adapters/AgentAdapters";
import {
  getReferenceDatasetIds,
  referenceEvaluationRecords,
  referenceSubmitMeta,
} from "@/modules/dataset/mock/DatasetFixtures";
import { normalizeDatasetIds } from "@/modules/dataset/lib/DatasetIdAliases";
import {
  resolvePublicDatasetName,
  resolvePublicDatasetNames,
} from "@/modules/dataset/lib";
import {
  MAX_SUBMIT_DATASET_COUNT,
  validateSubmitPayload,
} from "@/modules/submission/lib";

interface StoredEvaluationRecord {
  evaluationId: string;
  requestId: string;
  agentName: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  status: EvaluationStatus;
  publicToLeaderboard: boolean;
  datasetIds: string[];
  datasetNames: string[];
  submitMethod: "api" | "docker";
  score: number | null;
  ownerName: string;
  parameters: SubmitAgentPayload["parameters"];
  completedDatasetCount: number;
  pauseUsed: boolean;
  pauseDeadlineAt: string | null;
  finalReportAvailable: boolean;
  finalizationReason: EvaluationFinalizationReason | null;
  reportGeneratedAt: string | null;
  phaseStartedAt: string;
}

interface ResolvedEvaluationState {
  evaluationId: string;
  agentName: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  status: EvaluationStatus;
  publicToLeaderboard: boolean;
  datasetIds: string[];
  datasetNames: string[];
  submitMethod: "api" | "docker";
  score: number | null;
  ownerName: string;
  parameters: SubmitAgentPayload["parameters"];
  progressPercent: number;
  finalReportAvailable: boolean;
  finalizationReason: EvaluationFinalizationReason | null;
  progress: EvaluationProgress;
  controls: EvaluationControls;
  report: EvaluationReport | null;
}

interface ServiceError extends Error {
  code?: number;
}

const MOCK_PENDING_DELAY_MS = 2200;
const MOCK_DATASET_DURATION_MS = 3600;
const MOCK_CANCEL_DELAY_MS = 800;
const PAUSE_TIMEOUT_MS = 60 * 60 * 1000;
const SUBMIT_META_CACHE_KEY = "agents:submit-meta";
const useLiveSubmissionApi = !ApiConfig.enableApiMock;
const useLiveReferenceApi = !ApiConfig.enableApiMock;

const nowIso = (): string => new Date().toISOString();
const toTimestamp = (value: string): number => new Date(value).getTime();
const toIso = (value: number): string => new Date(value).toISOString();

const createServiceError = (message: string, code?: number): ServiceError => {
  const error = new Error(message) as ServiceError;
  error.code = code;
  return error;
};

const createSubmitMetaError = (): Error =>
  new Error("submit-meta 响应结构不符合新协议，请确认后端仅返回扁平结构。");

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

const sanitizeEvaluationRecord = (
  record: EvaluationRecord,
): EvaluationRecord => ({
  ...record,
  datasetNames: resolvePublicDatasetNames(
    record.datasetIds,
    record.datasetNames,
  ),
});

const sanitizeEvaluationDetail = (
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

const ensureSubmitMeta = (payload: unknown): SubmitMetaResponse => {
  if (!payload || typeof payload !== "object") {
    throw createSubmitMetaError();
  }

  const candidate = payload as Partial<SubmitMetaResponse>;

  if (
    !Array.isArray(candidate.supportedMethods) ||
    !candidate.difficulty ||
    !candidate.timeoutMinutes ||
    !candidate.retryEnabled ||
    !candidate.publicToLeaderboard
  ) {
    throw createSubmitMetaError();
  }

  return {
    supportedMethods: candidate.supportedMethods,
    difficulty: candidate.difficulty,
    timeoutMinutes: {
      ...candidate.timeoutMinutes,
      recommendedMax: candidate.timeoutMinutes.recommendedMax ?? 20,
    },
    retryEnabled: candidate.retryEnabled,
    publicToLeaderboard: candidate.publicToLeaderboard,
  };
};

const readStoredRecords = (): StoredEvaluationRecord[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.mock.evaluations);
    if (!raw) {
      return [];
    }

    return JSON.parse(raw) as StoredEvaluationRecord[];
  } catch {
    return [];
  }
};

const writeStoredRecords = (records: StoredEvaluationRecord[]): void => {
  localStorage.setItem(STORAGE_KEYS.mock.evaluations, JSON.stringify(records));
};

const getDatasetCount = (record: { datasetIds: string[] }): number =>
  Math.max(record.datasetIds.length, 1);

const clampPercent = (value: number): number =>
  Math.min(100, Math.max(0, Math.round(value)));

const computeScore = (
  record: {
    agentName: string;
    evaluationId: string;
    datasetIds: string[];
    parameters: SubmitAgentPayload["parameters"];
    submitMethod: "api" | "docker";
  },
  completedDatasetCount = record.datasetIds.length,
): number => {
  const completionRatio = completedDatasetCount / getDatasetCount(record);
  const datasetFactor = record.datasetIds.length * 1.8;
  const retryPenalty = record.parameters.retryEnabled ? 1.5 : 0;
  const difficultyBonus = record.parameters.difficulty * 7;
  const timeoutBonus = Math.min(record.parameters.timeoutMinutes, 24) * 0.18;
  const seed = record.agentName.length + record.evaluationId.length;
  const completionPenalty = (1 - completionRatio) * 10;
  const score =
    82 +
    datasetFactor +
    difficultyBonus +
    timeoutBonus -
    retryPenalty -
    completionPenalty +
    (seed % 4);

  return Number(Math.min(98.8, Math.max(70.6, score)).toFixed(1));
};

const buildMetrics = (
  score: number,
  submitMethod: "api" | "docker",
  retryEnabled: boolean,
): EvaluationMetric[] => {
  const attackDetection = Math.min(99, Math.round(score + 2));
  const policyStability = Math.min(
    97,
    Math.round(score - (retryEnabled ? 1 : 0)),
  );
  const executionBoundary = Math.min(
    98,
    Math.round(score + (submitMethod === "docker" ? 1 : 0)),
  );
  const responseSpeed = Math.max(
    68,
    Math.round(96 - (retryEnabled ? 1 : 0) * 1.4),
  );

  return [
    {
      name: "攻击检测率",
      value: `${attackDetection}%`,
      percentage: attackDetection,
      description: "识别恶意提示与异常工具响应的能力。",
    },
    {
      name: "策略稳定性",
      value: `${policyStability}%`,
      percentage: policyStability,
      description: "多轮攻击下仍保持安全边界的稳定程度。",
    },
    {
      name: "执行边界控制",
      value: `${executionBoundary}%`,
      percentage: executionBoundary,
      description: "面向越权调用和高风险动作的阻断能力。",
    },
    {
      name: "响应效率",
      value: `${responseSpeed}%`,
      percentage: responseSpeed,
      description: "在安全判定与服务时延之间的平衡表现。",
    },
  ];
};

void buildMetrics;

const buildReport = (record: {
  status: EvaluationStatus;
  finalReportAvailable: boolean;
  reportGeneratedAt: string | null;
  finalizationReason: EvaluationFinalizationReason | null;
  parameters: SubmitAgentPayload["parameters"];
  submitMethod: "api" | "docker";
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
  const safeScore = record.score ?? 0;
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
    generatedAt: record.reportGeneratedAt ?? nowIso(),
    warnings: [],
    metrics: [],
  };
  /*
  const summary =
    record.status === "completed"
      ? `本次评测共覆盖 ${totalDatasetCount} 个数据集，所有评测项已完成，核心安全指标表现稳定。`
      : `本次评测在完成 ${completedDatasetCount}/${totalDatasetCount} 个数据集后结束，以下报告仅基于已完成的评测数据。`;

  const warnings: string[] = [];
  if (record.parameters.retryEnabled) {
    warnings.push("已启用失败重试，建议复核高耗时场景下的重试副作用。");
  }
  if (record.finalizationReason === "terminated_by_user") {
    warnings.push("任务由用户终止，未完成的数据集不会计入最终报告。");
  }
  if (record.finalizationReason === "auto_terminated_after_pause_timeout") {
    warnings.push("任务在暂停超时后自动终止，报告仅覆盖已完成的数据集。");
  }

  return {
    generatedAt: record.reportGeneratedAt ?? nowIso(),
    summary,
    warnings,
    metrics: buildMetrics(
      record.score,
      record.submitMethod,
      record.parameters.retryEnabled,
    ),
  };
  */
};

const buildControls = (
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
  const phaseElapsed = Math.max(0, now - toTimestamp(record.phaseStartedAt));
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

const toEvaluationRecord = (
  state: ResolvedEvaluationState,
): EvaluationRecord => ({
  evaluationId: state.evaluationId,
  agentName: state.agentName,
  description: state.description,
  createdAt: state.createdAt,
  updatedAt: state.updatedAt,
  status: state.status,
  progressPercent: state.progressPercent,
  finalReportAvailable: state.finalReportAvailable,
  finalizationReason: state.finalizationReason,
  publicToLeaderboard: state.publicToLeaderboard,
  datasetIds: state.datasetIds,
  datasetNames: state.datasetNames,
  submitMethod: state.submitMethod,
  score: state.score,
  ownerName: state.ownerName,
  parameters: state.parameters,
});

const toEvaluationDetail = (
  state: ResolvedEvaluationState,
): EvaluationDetail => ({
  ...toEvaluationRecord(state),
  progress: state.progress,
  controls: state.controls,
  report: state.report,
});

const finalizeStoredRecord = (
  record: StoredEvaluationRecord,
  status: Extract<
    EvaluationStatus,
    "completed" | "terminated" | "canceled" | "failed"
  >,
  finalizationReason: EvaluationFinalizationReason,
  finalizedAt: string,
) => {
  record.status = status;
  record.updatedAt = finalizedAt;
  record.phaseStartedAt = finalizedAt;
  record.pauseDeadlineAt = null;
  record.finalizationReason = finalizationReason;
  record.finalReportAvailable =
    status === "completed" || status === "terminated";
  record.reportGeneratedAt = record.finalReportAvailable ? finalizedAt : null;
  record.score = record.finalReportAvailable
    ? computeScore(record, record.completedDatasetCount)
    : null;
};

const advanceStoredRecord = (
  record: StoredEvaluationRecord,
  now = Date.now(),
): boolean => {
  let changed = false;
  const totalDatasetCount = getDatasetCount(record);

  while (true) {
    switch (record.status) {
      case "pending": {
        const phaseEnd =
          toTimestamp(record.phaseStartedAt) + MOCK_PENDING_DELAY_MS;
        if (now < phaseEnd) {
          return changed;
        }

        record.status = "running";
        record.phaseStartedAt = toIso(phaseEnd);
        record.updatedAt = record.phaseStartedAt;
        changed = true;
        continue;
      }

      case "running":
      case "pausing":
      case "terminating": {
        const phaseEnd =
          toTimestamp(record.phaseStartedAt) + MOCK_DATASET_DURATION_MS;
        if (now < phaseEnd) {
          return changed;
        }

        record.completedDatasetCount = Math.min(
          record.completedDatasetCount + 1,
          totalDatasetCount,
        );
        record.updatedAt = toIso(phaseEnd);
        changed = true;

        if (record.status === "pausing") {
          record.status = "paused";
          record.phaseStartedAt = record.updatedAt;
          record.pauseDeadlineAt = toIso(phaseEnd + PAUSE_TIMEOUT_MS);
          continue;
        }

        if (record.status === "terminating") {
          finalizeStoredRecord(
            record,
            "terminated",
            "terminated_by_user",
            record.updatedAt,
          );
          return true;
        }

        if (record.completedDatasetCount >= totalDatasetCount) {
          finalizeStoredRecord(
            record,
            "completed",
            "completed",
            record.updatedAt,
          );
          return true;
        }

        record.status = "running";
        record.phaseStartedAt = record.updatedAt;
        continue;
      }

      case "paused": {
        if (
          record.pauseDeadlineAt &&
          now >= toTimestamp(record.pauseDeadlineAt)
        ) {
          finalizeStoredRecord(
            record,
            "terminated",
            "auto_terminated_after_pause_timeout",
            record.pauseDeadlineAt,
          );
          return true;
        }

        return changed;
      }

      case "canceling": {
        const phaseEnd =
          toTimestamp(record.phaseStartedAt) + MOCK_CANCEL_DELAY_MS;
        if (now < phaseEnd) {
          return changed;
        }

        finalizeStoredRecord(
          record,
          "canceled",
          "canceled_by_user",
          toIso(phaseEnd),
        );
        return true;
      }

      default:
        return changed;
    }
  }
};

const syncStoredRecords = (): StoredEvaluationRecord[] => {
  const records = readStoredRecords();
  let changed = false;
  const now = Date.now();

  const nextRecords = records.map((record) => {
    const nextRecord = { ...record };
    if (advanceStoredRecord(nextRecord, now)) {
      changed = true;
    }
    return nextRecord;
  });

  if (changed) {
    writeStoredRecords(nextRecords);
  }

  return nextRecords;
};

const buildResolvedStateFromStored = (
  record: StoredEvaluationRecord,
  now = Date.now(),
): ResolvedEvaluationState => {
  const progress = buildProgress(record, record.status, now);
  const controls = buildControls(record.status, record.pauseUsed);
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

const buildResolvedStateFromReference = (
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
    controls: buildControls(record.status, false),
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
  /*

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
    controls: buildControls(record.status, false),
    report:
      record.finalReportAvailable && typeof record.score === "number"
        ? {
            generatedAt: record.updatedAt,
            summary: `本次评测共覆盖 ${record.datasetIds.length} 个数据集，核心安全指标表现稳定。`,
            warnings: [],
            metrics: buildMetrics(
              record.score,
              record.submitMethod,
              record.parameters.retryEnabled,
            ),
          }
        : null,
  };
  */
};

const getMergedRecords = (): EvaluationRecord[] => {
  const storedRecords = syncStoredRecords().map((record) =>
    toEvaluationRecord(buildResolvedStateFromStored(record)),
  );
  const normalizedReferenceRecords = referenceEvaluationRecords.map((record) =>
    adaptEvaluationRecord(record),
  );

  return [...storedRecords, ...normalizedReferenceRecords].sort(
    (left, right) => toTimestamp(right.createdAt) - toTimestamp(left.createdAt),
  );
};

const getReferenceMeta = async (): Promise<SubmitMetaResponse> => {
  if (!ApiConfig.enableApiMock) {
    return withMemoryCache(
      SUBMIT_META_CACHE_KEY,
      async () => {
        const response = await request.get<unknown>("/agents/submit-meta");

        if (!response.success || !response.data) {
          throw createServiceError(
            response.message || "提交元数据加载失败。",
            response.code,
          );
        }

        return adaptSubmitMeta(response.data as never);
      },
      { force: false },
    );
  }

  if (useLiveReferenceApi) {
    const response = await request.get<SubmitMetaResponse>(
      "/agents/submit-meta",
    );

    if (!response.success || !response.data) {
      throw createServiceError(
        response.message || "提交元数据加载失败。",
        response.code,
      );
    }

    return ensureSubmitMeta(response.data);
  }

  const result = await resolveMockEnvelope(
    createSuccessEnvelope(referenceSubmitMeta),
  );
  return ensureSubmitMeta(result.data);
};

const getStoredRecordById = (
  evaluationId: string,
): StoredEvaluationRecord | null => {
  const records = syncStoredRecords();
  const record = records.find((item) => item.evaluationId === evaluationId);
  return record ? { ...record } : null;
};

const updateStoredRecord = (nextRecord: StoredEvaluationRecord): void => {
  const records = syncStoredRecords();
  const nextRecords = records.map((record) =>
    record.evaluationId === nextRecord.evaluationId ? nextRecord : record,
  );
  writeStoredRecords(nextRecords);
};

const ensureMockActionAllowed = (
  record: StoredEvaluationRecord,
  action: EvaluationAction,
) => {
  const controls = buildControls(record.status, record.pauseUsed);

  if (action === "pause") {
    if (record.pauseUsed) {
      throw createServiceError("该任务已使用过暂停机会，不能再次暂停。", 40902);
    }
    if (!controls.canPause) {
      throw createServiceError(`当前状态不允许执行 ${action} 操作。`, 40901);
    }
    return;
  }

  if (action === "resume" && !controls.canResume) {
    throw createServiceError(`当前状态不允许执行 ${action} 操作。`, 40901);
  }

  if (action === "terminate" && !controls.canTerminate) {
    throw createServiceError(`当前状态不允许执行 ${action} 操作。`, 40901);
  }

  if (action === "cancel" && !controls.canCancel) {
    throw createServiceError(`当前状态不允许执行 ${action} 操作。`, 40901);
  }
};

export const getSubmitMeta = async (): Promise<SubmitMetaResponse> =>
  getReferenceMeta();

export const precheckAgent = async (
  payload: SubmitAgentPayload,
): Promise<PrecheckResponse> => {
  if (useLiveSubmissionApi) {
    const response = await request.post<PrecheckResponse>(
      "/agents/precheck",
      buildSubmitAgentApiPayload(payload),
    );

    if (!response.success || !response.data) {
      throw createServiceError(
        response.message || "预检查失败。",
        response.code,
      );
    }

    return response.data;
  }

  const meta = await getReferenceMeta();
  const validation = validateSubmitPayload(
    payload,
    meta,
    getReferenceDatasetIds(),
  );

  if (!validation.valid) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40002, validation.errors[0] || "参数校验失败。", {
        ok: false,
        warnings: validation.errors,
      }),
    );
    throw createServiceError(result.message, result.code);
  }

  const warnings: string[] = [];
  if (payload.publicToLeaderboard) {
    warnings.push("本次结果将进入公开排行榜，请确认描述中不包含敏感信息。");
  }

  const recommendedMax = meta.timeoutMinutes.recommendedMax ?? 20;
  if (payload.parameters.timeoutMinutes > recommendedMax) {
    warnings.push(
      `当前超时时间高于建议值 ${recommendedMax}，评测排队与执行耗时可能更长。`,
    );
  }

  const result = await resolveMockEnvelope(
    createSuccessEnvelope({
      ok: true,
      warnings,
    }),
  );

  return result.data;
};

export const submitAgent = async (
  payload: SubmitAgentPayload,
): Promise<SubmitResponse> => {
  if (useLiveSubmissionApi) {
    const response = await request.post<SubmitResponse>(
      "/agents/submit",
      buildSubmitAgentApiPayload(payload),
    );

    if (!response.success || !response.data) {
      throw createServiceError(
        response.message || "提交失败，请稍后重试。",
        response.code,
      );
    }

    return response.data;
  }

  const meta = await getReferenceMeta();
  const validation = validateSubmitPayload(
    payload,
    meta,
    getReferenceDatasetIds(),
  );

  if (!validation.valid) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40002, validation.errors[0] || "参数校验失败。", {
        evaluationId: "",
        status: "pending" as EvaluationStatus,
        createdAt: "",
      }),
      { delay: 520 },
    );
    throw createServiceError(result.message, result.code);
  }

  const existing = syncStoredRecords().find(
    (record) => record.requestId === payload.requestId,
  );
  if (existing) {
    const result = await resolveMockEnvelope(
      createSuccessEnvelope({
        evaluationId: existing.evaluationId,
        status: existing.status,
        createdAt: existing.createdAt,
      }),
      { delay: 520 },
    );
    return result.data;
  }

  const now = nowIso();
  const datasetIds = normalizeDatasetIds(
    Array.from(new Set(payload.selectedDatasetIds)).slice(
      0,
      MAX_SUBMIT_DATASET_COUNT,
    ),
  );
  const record: StoredEvaluationRecord = {
    evaluationId: `eval_${Date.now()}`,
    requestId: payload.requestId,
    agentName: payload.agentName.trim(),
    description: payload.description?.trim(),
    createdAt: now,
    updatedAt: now,
    status: "pending",
    publicToLeaderboard: payload.publicToLeaderboard,
    datasetIds,
    datasetNames: resolvePublicDatasetNames(datasetIds),
    submitMethod: payload.submitMethod,
    score: null,
    ownerName: "当前用户",
    parameters: payload.parameters,
    completedDatasetCount: 0,
    pauseUsed: false,
    pauseDeadlineAt: null,
    finalReportAvailable: false,
    finalizationReason: null,
    reportGeneratedAt: null,
    phaseStartedAt: now,
  };

  writeStoredRecords([record, ...syncStoredRecords()]);

  const result = await resolveMockEnvelope(
    createSuccessEnvelope({
      evaluationId: record.evaluationId,
      status: record.status,
      createdAt: record.createdAt,
    }),
    { delay: 780 },
  );

  return result.data;
};

export const getEvaluationRecords = async (): Promise<EvaluationRecord[]> => {
  if (useLiveSubmissionApi) {
    const response = await request.get<EvaluationRecord[]>("/evaluations");

    if (!response.success || !response.data) {
      throw createServiceError(
        response.message || "评测记录加载失败。",
        response.code,
      );
    }

    return (response.data as unknown[]).map((item) =>
      sanitizeEvaluationRecord(adaptEvaluationRecord(item)),
    );
  }

  const result = await resolveMockEnvelope(
    createSuccessEnvelope(getMergedRecords()),
  );
  return result.data.map(sanitizeEvaluationRecord);
};

export const getEvaluationDetail = async (
  evaluationId: string,
): Promise<EvaluationDetail> => {
  if (useLiveSubmissionApi) {
    const response = await request.get<EvaluationDetail>(
      `/evaluations/${evaluationId}`,
    );

    if (!response.success || !response.data) {
      throw createServiceError(
        response.message || "评测详情加载失败。",
        response.code,
      );
    }

    return sanitizeEvaluationDetail(adaptEvaluationDetail(response.data));
  }

  const storedRecord = getStoredRecordById(evaluationId);
  if (storedRecord) {
    const result = await resolveMockEnvelope(
      createSuccessEnvelope(
        toEvaluationDetail(buildResolvedStateFromStored(storedRecord)),
      ),
    );
    return sanitizeEvaluationDetail(result.data);
  }

  const referenceRecord = referenceEvaluationRecords.find(
    (item) => item.evaluationId === evaluationId,
  );
  if (referenceRecord) {
    const result = await resolveMockEnvelope(
      createSuccessEnvelope(
        toEvaluationDetail(buildResolvedStateFromReference(referenceRecord)),
      ),
    );
    return sanitizeEvaluationDetail(result.data);
  }

  const result = await resolveMockEnvelope(
    createErrorEnvelope(40400, "评测记录不存在。", null),
  );
  throw createServiceError(result.message, result.code);
};

export const postEvaluationAction = async (
  evaluationId: string,
  action: EvaluationAction,
): Promise<EvaluationDetail> => {
  if (useLiveSubmissionApi) {
    const response = await request.post<EvaluationDetail>(
      `/evaluations/${evaluationId}/actions`,
      { action } as EvaluationActionRequest,
    );

    if (!response.success || !response.data) {
      throw createServiceError(
        response.message || "任务操作失败。",
        response.code,
      );
    }

    return sanitizeEvaluationDetail(adaptEvaluationDetail(response.data));
  }

  const storedRecord = getStoredRecordById(evaluationId);
  if (!storedRecord) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(
        40400,
        `评测任务 ${evaluationId} 不存在或已被删除。`,
        null,
      ),
    );
    throw createServiceError(result.message, result.code);
  }

  ensureMockActionAllowed(storedRecord, action);

  const nextRecord = { ...storedRecord };
  const actedAt = nowIso();

  switch (action) {
    case "pause":
      nextRecord.status = "pausing";
      nextRecord.pauseUsed = true;
      nextRecord.updatedAt = actedAt;
      break;
    case "resume":
      nextRecord.status = "running";
      nextRecord.phaseStartedAt = actedAt;
      nextRecord.pauseDeadlineAt = null;
      nextRecord.updatedAt = actedAt;
      break;
    case "terminate":
      if (nextRecord.status === "paused") {
        finalizeStoredRecord(
          nextRecord,
          "terminated",
          "terminated_by_user",
          actedAt,
        );
      } else {
        nextRecord.status = "terminating";
        nextRecord.updatedAt = actedAt;
      }
      break;
    case "cancel":
      nextRecord.status = "canceling";
      nextRecord.phaseStartedAt = actedAt;
      nextRecord.pauseDeadlineAt = null;
      nextRecord.updatedAt = actedAt;
      break;
  }

  advanceStoredRecord(nextRecord, Date.now());
  updateStoredRecord(nextRecord);

  const result = await resolveMockEnvelope(
    createSuccessEnvelope(
      toEvaluationDetail(buildResolvedStateFromStored(nextRecord)),
    ),
    { delay: 420 },
  );
  return sanitizeEvaluationDetail(result.data);
};
