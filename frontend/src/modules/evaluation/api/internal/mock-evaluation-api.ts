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

export const getMockEvaluationScoreTrend = async (
  scope: EvaluationScoreTrendScope,
): Promise<EvaluationScoreTrend> => {
  const records = getMergedRecords()
    .filter(isTrendRecord)
    .sort((left, right) => getTrendDateTime(left) - getTrendDateTime(right));
  const scopedRecords = scope === "recent10" ? records.slice(-10) : records;

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
      items: scopedRecords.map((record) => ({
        evaluationId: record.evaluationId,
        agentName: record.agentName,
        createdAt: record.createdAt,
        finishedAt: record.finishedAt ?? record.updatedAt,
        scores: buildTrendScores(record),
      })),
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
