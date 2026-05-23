import {
  createErrorEnvelope,
  createSuccessEnvelope,
  resolveMockEnvelope,
} from "@/shared/api/mock-api-utils";
import type {
  EvaluationDetail,
  EvaluationReportPayload,
  EvaluationRecord,
} from "@/shared/types/agent-types";
import { referenceEvaluationRecords } from "@/modules/evaluation/mock/evaluation-fixtures";
import {
  buildMockReportPayload,
  buildResolvedStateFromReference,
  sanitizeEvaluationDetail,
  sanitizeEvaluationRecord,
} from "./evaluation-service-view";
import { createServiceError, toEvaluationDetail } from "./evaluation-service-shared";

const getReferenceRecord = (evaluationId: string): EvaluationRecord | null =>
  referenceEvaluationRecords.find((item) => item.evaluationId === evaluationId) ??
  null;

const toMockEvaluationDetail = (record: EvaluationRecord): EvaluationDetail => {
  const detail = toEvaluationDetail(buildResolvedStateFromReference(record));
  return {
    ...sanitizeEvaluationDetail(detail),
    controls: {
      ...detail.controls,
      canPause: false,
      canResume: false,
      canTerminate: false,
      canCancel: false,
    },
    downloads: {
      sampleDetailsUrl: null,
    },
  };
};

export const getMockEvaluationRecords = async (): Promise<
  EvaluationRecord[]
> => {
  const result = await resolveMockEnvelope(
    createSuccessEnvelope(
      [...referenceEvaluationRecords].sort(
        (left, right) =>
          new Date(right.createdAt).getTime() -
          new Date(left.createdAt).getTime(),
      ),
    ),
  );

  return result.data.map(sanitizeEvaluationRecord);
};

export const getMockEvaluationDetail = async (
  evaluationId: string,
): Promise<EvaluationDetail> => {
  const referenceRecord = getReferenceRecord(evaluationId);
  if (referenceRecord) {
    const result = await resolveMockEnvelope(
      createSuccessEnvelope(toMockEvaluationDetail(referenceRecord)),
    );
    return result.data;
  }

  const result = await resolveMockEnvelope(
    createErrorEnvelope(40400, "评测记录不存在。", null),
  );
  throw createServiceError(result.message, result.code);
};

export const getMockEvaluationReport = async (
  evaluationId: string,
): Promise<EvaluationReportPayload> => {
  const referenceRecord = getReferenceRecord(evaluationId);
  const state = referenceRecord
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
