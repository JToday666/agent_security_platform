import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
} from "@/shared/api/mock-api-utils";
import type {
  EvaluationAction,
  EvaluationDetail,
  EvaluationRecord,
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
  const datasetIds = normalizeDatasetIds(
    Array.from(new Set(payload.selectedDatasetIds)).slice(
      0,
      MAX_SUBMIT_DATASET_COUNT,
    ),
  );

  return {
    evaluationId: `eval_${Date.now()}`,
    requestId: payload.requestId,
    agentName: payload.agentName.trim(),
    description: payload.description?.trim(),
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

export const submitMockAgent = async (
  payload: SubmitAgentPayload,
): Promise<SubmitResponse> => {
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
