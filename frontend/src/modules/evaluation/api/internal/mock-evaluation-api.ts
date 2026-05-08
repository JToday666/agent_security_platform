import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
} from "@/shared/api/mock-api-utils";
import type {
  EvaluationAction,
  EvaluationDetail,
  EvaluationReportPayload,
  EvaluationRecord,
  EvaluationScoreTrend,
  EvaluationScoreTrendScope,
  EvaluationStatus,
  PrecheckResponse,
  SubmitAgentPayload,
  SubmitMetaResponse,
  SubmitResponse,
} from "@/shared/types/agent-types";
import {
  getReferenceDatasetIds,
  referenceEvaluationRecords,
  referenceSubmitMeta,
} from "@/modules/dataset/mock/dataset-fixtures";
import { normalizeDatasetIds } from "@/modules/dataset/model/dataset-id-aliases";
import { resolvePublicDatasetNames } from "@/modules/dataset/lib/dataset-display-utils";
import {
  MAX_SUBMIT_DATASET_COUNT,
  validateSubmitPayload,
} from "@/modules/submission/model/parameter-validator";
import {
  getStoredMockAgentById,
  getStoredMockAgents,
} from "@/modules/agent/api/internal/mock-agent-store";
import { adaptEvaluationRecord } from "@/modules/evaluation/api/adapters/agent-adapters";
import {
  advanceStoredRecord,
  ensureMockActionAllowed,
  findStoredRecordByRequestId,
  finalizeStoredRecord,
  getStoredRecordById,
  prependStoredRecord,
  syncStoredRecords,
  updateStoredRecord,
} from "./mock-evaluation-store";
import {
  buildMockReportPayload,
  buildResolvedStateFromReference,
  buildResolvedStateFromStored,
  sanitizeEvaluationDetail,
  sanitizeEvaluationRecord,
} from "./evaluation-service-view";
import {
  createServiceError,
  ensureSubmitMeta,
  nowIso,
  toEvaluationDetail,
  toEvaluationRecord,
  type StoredEvaluationRecord,
} from "./evaluation-service-shared";

const MOCK_SUBMIT_VALIDATION_DELAY_MS = 520;
const MOCK_SUBMIT_CREATED_DELAY_MS = 780;
const MOCK_ACTION_DELAY_MS = 420;

type MockTrendItem = EvaluationScoreTrend["items"][number];

const MOCK_TREND_ITEMS: MockTrendItem[] = [
  {
    evaluationId: "eval_20260330_004",
    agentName: "Ops Control Auditor",
    createdAt: "2026-03-18T03:20:00Z",
    finishedAt: "2026-03-18T03:58:00Z",
    scores: {
      conservativeScore: 82.4,
      performanceScore: 85.1,
      hardScore: 70.8,
      confidence: 74.2,
      unsafeRate: 12.6,
      completionScore: 88.2,
      safetyScore: 84.1,
      timeScore: 78.5,
    },
  },
  {
    evaluationId: "eval_20260331_003",
    agentName: "Civic Safety Writer",
    createdAt: "2026-03-20T06:40:00Z",
    finishedAt: "2026-03-20T07:04:00Z",
    scores: {
      conservativeScore: 84.7,
      performanceScore: 87.2,
      hardScore: 73.6,
      confidence: 75.8,
      unsafeRate: 10.8,
      completionScore: 89.4,
      safetyScore: 85.9,
      timeScore: 80.2,
    },
  },
  {
    evaluationId: "eval_20260401_002",
    agentName: "Boundary Sentinel",
    createdAt: "2026-03-22T09:10:00Z",
    finishedAt: "2026-03-22T09:43:00Z",
    scores: {
      conservativeScore: 86.1,
      performanceScore: 88.5,
      hardScore: 76.4,
      confidence: 78.1,
      unsafeRate: 9.5,
      completionScore: 90.8,
      safetyScore: 87.2,
      timeScore: 81.6,
    },
  },
  {
    evaluationId: "eval_20260402_001",
    agentName: "Guardian Mesh v2.4",
    createdAt: "2026-03-24T01:15:00Z",
    finishedAt: "2026-03-24T01:47:00Z",
    scores: {
      conservativeScore: 88.9,
      performanceScore: 91.2,
      hardScore: 79.1,
      confidence: 80.5,
      unsafeRate: 8.1,
      completionScore: 92.4,
      safetyScore: 90.2,
      timeScore: 82.4,
    },
  },
  {
    evaluationId: "eval_20260330_004",
    agentName: "Ops Control Auditor",
    createdAt: "2026-03-26T03:20:00Z",
    finishedAt: "2026-03-26T03:55:00Z",
    scores: {
      conservativeScore: 87.3,
      performanceScore: 90.6,
      hardScore: 78.2,
      confidence: 81.4,
      unsafeRate: 8.9,
      completionScore: 91.8,
      safetyScore: 88.6,
      timeScore: 83.1,
    },
  },
  {
    evaluationId: "eval_20260331_003",
    agentName: "Civic Safety Writer",
    createdAt: "2026-03-28T06:40:00Z",
    finishedAt: "2026-03-28T07:02:00Z",
    scores: {
      conservativeScore: 89.5,
      performanceScore: 91.9,
      hardScore: 80.3,
      confidence: 82.7,
      unsafeRate: 7.4,
      completionScore: 93.1,
      safetyScore: 90.4,
      timeScore: 84.3,
    },
  },
  {
    evaluationId: "eval_20260401_002",
    agentName: "Boundary Sentinel",
    createdAt: "2026-03-30T09:10:00Z",
    finishedAt: "2026-03-30T09:45:00Z",
    scores: {
      conservativeScore: 90.8,
      performanceScore: 93.2,
      hardScore: 82.5,
      confidence: 84.6,
      unsafeRate: 6.5,
      completionScore: 94.2,
      safetyScore: 91.8,
      timeScore: 85.6,
    },
  },
  {
    evaluationId: "eval_20260402_001",
    agentName: "Guardian Mesh v2.4",
    createdAt: "2026-04-01T01:15:00Z",
    finishedAt: "2026-04-01T01:46:00Z",
    scores: {
      conservativeScore: 92.4,
      performanceScore: 94.5,
      hardScore: 84.1,
      confidence: 86.2,
      unsafeRate: 5.8,
      completionScore: 95.3,
      safetyScore: 93.2,
      timeScore: 86.8,
    },
  },
  {
    evaluationId: "eval_20260401_002",
    agentName: "Boundary Sentinel",
    createdAt: "2026-04-02T09:10:00Z",
    finishedAt: "2026-04-02T09:44:00Z",
    scores: {
      conservativeScore: 91.7,
      performanceScore: 93.8,
      hardScore: 83.6,
      confidence: 86.9,
      unsafeRate: 6.1,
      completionScore: 94.7,
      safetyScore: 92.4,
      timeScore: 87.1,
    },
  },
  {
    evaluationId: "eval_20260402_001",
    agentName: "Guardian Mesh v2.4",
    createdAt: "2026-04-03T01:15:00Z",
    finishedAt: "2026-04-03T01:45:00Z",
    scores: {
      conservativeScore: 94.2,
      performanceScore: 96.1,
      hardScore: 86.4,
      confidence: 89.3,
      unsafeRate: 4.4,
      completionScore: 96.8,
      safetyScore: 94.9,
      timeScore: 88.2,
    },
  },
];

const getReferenceMeta = async (): Promise<SubmitMetaResponse> => {
  const result = await resolveMockEnvelope(
    createSuccessEnvelope(referenceSubmitMeta),
  );

  return ensureSubmitMeta(result.data);
};

const getMergedRecords = (): EvaluationRecord[] => {
  const storedRecords = syncStoredRecords().map((record) =>
    toEvaluationRecord(buildResolvedStateFromStored(record)),
  );
  const normalizedReferenceRecords = referenceEvaluationRecords.map((record) =>
    adaptEvaluationRecord(record),
  );

  return [...storedRecords, ...normalizedReferenceRecords].sort(
    (left, right) =>
      new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime(),
  );
};

const createStoredRecord = (
  payload: SubmitAgentPayload,
): StoredEvaluationRecord => {
  const createdAt = nowIso();
  const agent = payload.agentId
    ? getStoredMockAgentById(payload.agentId)
    : null;
  const datasetIds = normalizeDatasetIds(
    Array.from(new Set(payload.selectedDatasetIds)).slice(
      0,
      MAX_SUBMIT_DATASET_COUNT,
    ),
  );

  return {
    evaluationId: `eval_${Date.now()}`,
    requestId: payload.requestId,
    agentName: agent?.name ?? "未命名智能体",
    description: agent?.description,
    createdAt,
    updatedAt: createdAt,
    status: "pending",
    publicToLeaderboard: true,
    leaderboardDisplayMode: payload.leaderboardDisplayMode,
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
    phaseStartedAt: createdAt,
  };
};

export const getMockSubmitMeta = async (): Promise<SubmitMetaResponse> =>
  getReferenceMeta();

export const precheckMockAgent = async (
  payload: SubmitAgentPayload,
): Promise<PrecheckResponse> => {
  const meta = await getReferenceMeta();
  const activeAgentIds = getStoredMockAgents()
    .filter((agent) => agent.status === "active")
    .map((agent) => agent.agentId);
  const validation = validateSubmitPayload(
    payload,
    meta,
    getReferenceDatasetIds(),
    activeAgentIds,
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
  warnings.push(
    payload.leaderboardDisplayMode === "anonymous"
      ? "本次结果将进入排行榜，榜单仅展示匿名身份。"
      : "本次结果将进入排行榜，并展示智能体公开名称。",
  );

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

export const submitMockAgent = async (
  payload: SubmitAgentPayload,
): Promise<SubmitResponse> => {
  const meta = await getReferenceMeta();
  const activeAgentIds = getStoredMockAgents()
    .filter((agent) => agent.status === "active")
    .map((agent) => agent.agentId);
  const validation = validateSubmitPayload(
    payload,
    meta,
    getReferenceDatasetIds(),
    activeAgentIds,
  );

  if (!validation.valid) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40002, validation.errors[0] || "参数校验失败。", {
        evaluationId: "",
        status: "pending" as EvaluationStatus,
        createdAt: "",
      }),
      { delay: MOCK_SUBMIT_VALIDATION_DELAY_MS },
    );
    throw createServiceError(result.message, result.code);
  }

  const existing = findStoredRecordByRequestId(payload.requestId);
  if (existing) {
    const result = await resolveMockEnvelope(
      createSuccessEnvelope({
        evaluationId: existing.evaluationId,
        status: existing.status,
        createdAt: existing.createdAt,
      }),
      { delay: MOCK_SUBMIT_VALIDATION_DELAY_MS },
    );

    return result.data;
  }

  const record = createStoredRecord(payload);
  prependStoredRecord(record);

  const result = await resolveMockEnvelope(
    createSuccessEnvelope({
      evaluationId: record.evaluationId,
      status: record.status,
      createdAt: record.createdAt,
    }),
    { delay: MOCK_SUBMIT_CREATED_DELAY_MS },
  );

  return result.data;
};

export const getMockEvaluationRecords = async (): Promise<
  EvaluationRecord[]
> => {
  const result = await resolveMockEnvelope(
    createSuccessEnvelope(getMergedRecords()),
  );

  return result.data.map(sanitizeEvaluationRecord);
};

const buildTrendScores = (record: EvaluationRecord) => {
  const score = record.score ?? 0;
  const datasetFactor = Math.min(record.datasetIds.length * 2.6, 12);

  return {
    conservativeScore: Number(score.toFixed(1)),
    performanceScore: Number(Math.min(99, score + 3.4).toFixed(1)),
    hardScore: Number(Math.max(0, score - 10.8).toFixed(1)),
    confidence: Number(Math.min(96, 68 + datasetFactor).toFixed(1)),
    unsafeRate: Number(Math.max(1.2, (100 - score) * 0.24).toFixed(1)),
    completionScore: Number(Math.min(99, score + 5.1).toFixed(1)),
    safetyScore: Number(Math.min(99, score + 1.8).toFixed(1)),
    timeScore: Number(
      Math.max(52, 88 - record.parameters.timeoutMinutes * 0.8).toFixed(1),
    ),
  };
};

const isTrendRecord = (record: EvaluationRecord): boolean =>
  typeof record.score === "number" &&
  (record.finalReportAvailable ||
    record.status === "completed" ||
    record.status === "terminated");

const getTrendDateTime = (record: EvaluationRecord): number => {
  const value = record.finishedAt ?? record.updatedAt ?? record.createdAt;
  const time = new Date(value).getTime();
  return Number.isNaN(time) ? 0 : time;
};

const getTrendItemDateTime = (item: MockTrendItem): number => {
  const value = item.finishedAt ?? item.createdAt;
  const time = new Date(value).getTime();
  return Number.isNaN(time) ? 0 : time;
};

const buildTrendItemFromRecord = (record: EvaluationRecord): MockTrendItem => ({
  evaluationId: record.evaluationId,
  agentName: record.agentName,
  createdAt: record.createdAt,
  finishedAt: record.finishedAt ?? record.updatedAt,
  scores: buildTrendScores(record),
});

export const getMockEvaluationScoreTrend = async (
  scope: EvaluationScoreTrendScope,
): Promise<EvaluationScoreTrend> => {
  const dynamicItems = getMergedRecords()
    .filter(isTrendRecord)
    .sort((left, right) => getTrendDateTime(left) - getTrendDateTime(right))
    .map(buildTrendItemFromRecord);
  const dynamicKeys = new Set(
    dynamicItems.map((item) => `${item.evaluationId}:${item.finishedAt}`),
  );
  const seedItems = MOCK_TREND_ITEMS.filter(
    (item) => !dynamicKeys.has(`${item.evaluationId}:${item.finishedAt}`),
  );
  const items = [...seedItems, ...dynamicItems].sort(
    (left, right) => getTrendItemDateTime(left) - getTrendItemDateTime(right),
  );
  const scopedItems = scope === "recent10" ? items.slice(-10) : items;

  const result = await resolveMockEnvelope(
    createSuccessEnvelope({
      scope,
      defaultScope: "recent10",
      defaultView: "capability",
      views: {
        capability: {
          label: "能力视图",
          metrics: ["conservativeScore", "performanceScore", "hardScore"],
        },
        risk: {
          label: "风险视图",
          metrics: ["conservativeScore", "confidence", "unsafeRate"],
        },
      },
      items: scopedItems,
    } satisfies EvaluationScoreTrend),
  );

  return result.data;
};

export const getMockEvaluationDetail = async (
  evaluationId: string,
): Promise<EvaluationDetail> => {
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

export const getMockEvaluationReport = async (
  evaluationId: string,
): Promise<EvaluationReportPayload> => {
  const storedRecord = getStoredRecordById(evaluationId);
  const referenceRecord = referenceEvaluationRecords.find(
    (item) => item.evaluationId === evaluationId,
  );
  const state = storedRecord
    ? buildResolvedStateFromStored(storedRecord)
    : referenceRecord
      ? buildResolvedStateFromReference(referenceRecord)
      : null;
  const report = state ? buildMockReportPayload(state) : null;

  if (!report) {
    const result = await resolveMockEnvelope(
      createErrorEnvelope(40902, "评测报告尚未生成。", {
        evaluationId,
        status: state?.status ?? "pending",
      }),
    );
    throw createServiceError(result.message, result.code);
  }

  const result = await resolveMockEnvelope(createSuccessEnvelope(report));
  return result.data;
};

export const downloadMockEvaluationSampleDetails = async (
  evaluationId: string,
) => {
  const result = await resolveMockEnvelope(
    createErrorEnvelope(40400, `样本明细文件不存在：${evaluationId}`, null),
  );
  throw createServiceError(result.message, result.code);
};

export const postMockEvaluationAction = async (
  evaluationId: string,
  action: EvaluationAction,
): Promise<EvaluationDetail> => {
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
    { delay: MOCK_ACTION_DELAY_MS },
  );

  return sanitizeEvaluationDetail(result.data);
};
