import type {
  EvaluationAction,
  EvaluationFinalizationReason,
  EvaluationStatus,
} from "@/shared/types/agent-types";
import { STORAGE_KEYS } from "@/shared/constants/storage-keys";
import {
  computeScore,
  createServiceError,
  getDatasetCount,
  MOCK_CANCEL_DELAY_MS,
  MOCK_DATASET_DURATION_MS,
  MOCK_PENDING_DELAY_MS,
  PAUSE_TIMEOUT_MS,
  toIso,
  toTimestamp,
  type StoredEvaluationRecord,
} from "./evaluation-service-shared";
import { buildEvaluationControls } from "@/modules/evaluation/model/evaluation-controls";

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

export const writeStoredRecords = (records: StoredEvaluationRecord[]): void => {
  localStorage.setItem(STORAGE_KEYS.mock.evaluations, JSON.stringify(records));
};

export const finalizeStoredRecord = (
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

export const advanceStoredRecord = (
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

export const syncStoredRecords = (): StoredEvaluationRecord[] => {
  const records = readStoredRecords();
  let changed = false;
  const now = Date.now();

  const nextRecords = records.map((record) => {
    const leaderboardDisplayMode: StoredEvaluationRecord["leaderboardDisplayMode"] =
      record.leaderboardDisplayMode === "anonymous" ? "anonymous" : "public";
    const nextRecord: StoredEvaluationRecord = {
      ...record,
      leaderboardDisplayMode,
    };
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

export const getStoredRecordById = (
  evaluationId: string,
): StoredEvaluationRecord | null => {
  const records = syncStoredRecords();
  const record = records.find((item) => item.evaluationId === evaluationId);
  return record ? { ...record } : null;
};

export const updateStoredRecord = (
  nextRecord: StoredEvaluationRecord,
): void => {
  const records = syncStoredRecords();
  const nextRecords = records.map((record) =>
    record.evaluationId === nextRecord.evaluationId ? nextRecord : record,
  );
  writeStoredRecords(nextRecords);
};

export const findStoredRecordByRequestId = (
  requestId: string,
): StoredEvaluationRecord | null => {
  const record = syncStoredRecords().find(
    (item) => item.requestId === requestId,
  );
  return record ? { ...record } : null;
};

export const prependStoredRecord = (record: StoredEvaluationRecord): void => {
  writeStoredRecords([record, ...syncStoredRecords()]);
};

export const ensureMockActionAllowed = (
  record: StoredEvaluationRecord,
  action: EvaluationAction,
) => {
  const controls = buildEvaluationControls(record.status, record.pauseUsed);

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
