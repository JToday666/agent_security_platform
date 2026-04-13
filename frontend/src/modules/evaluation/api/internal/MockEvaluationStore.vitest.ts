import { describe, expect, it } from "vitest";
import {
  advanceStoredRecord,
  finalizeStoredRecord,
} from "./MockEvaluationStore";
import type { StoredEvaluationRecord } from "./EvaluationServiceShared";

const createStoredRecord = (
  overrides: Partial<StoredEvaluationRecord> = {},
): StoredEvaluationRecord => ({
  evaluationId: "eval_test_001",
  requestId: "submit_test_001",
  agentName: "Guardian Mesh",
  description: "mock evaluation",
  createdAt: "2026-04-01T00:00:00.000Z",
  updatedAt: "2026-04-01T00:00:00.000Z",
  status: "pending",
  publicToLeaderboard: true,
  datasetIds: ["A1", "B3"],
  datasetNames: ["A1", "B3"],
  submitMethod: "api",
  score: null,
  ownerName: "tester",
  parameters: {
    difficulty: 0.5,
    timeoutMinutes: 15,
    retryEnabled: false,
  },
  completedDatasetCount: 0,
  pauseUsed: false,
  pauseDeadlineAt: null,
  finalReportAvailable: false,
  finalizationReason: null,
  reportGeneratedAt: null,
  phaseStartedAt: "2026-04-01T00:00:00.000Z",
  ...overrides,
});

describe("MockEvaluationStore", () => {
  it("moves pending records into running after the queue delay", () => {
    const record = createStoredRecord();
    const changed = advanceStoredRecord(
      record,
      Date.parse(record.phaseStartedAt) + 3_000,
    );

    expect(changed).toBe(true);
    expect(record.status).toBe("running");
    expect(record.completedDatasetCount).toBe(0);
    expect(record.pauseDeadlineAt).toBeNull();
    expect(record.updatedAt).not.toBe("2026-04-01T00:00:00.000Z");
  });

  it("converts pausing records into paused state after the active dataset completes", () => {
    const record = createStoredRecord({
      status: "pausing",
      pauseUsed: true,
    });
    const changed = advanceStoredRecord(
      record,
      Date.parse(record.phaseStartedAt) + 4_000,
    );

    expect(changed).toBe(true);
    expect(record.status).toBe("paused");
    expect(record.completedDatasetCount).toBe(1);
    expect(record.pauseDeadlineAt).not.toBeNull();
  });

  it("marks terminal mock records with report metadata and score", () => {
    const record = createStoredRecord({
      completedDatasetCount: 2,
      status: "running",
    });
    finalizeStoredRecord(
      record,
      "completed",
      "completed",
      "2026-04-01T00:10:00.000Z",
    );

    expect(record.status).toBe("completed");
    expect(record.finalReportAvailable).toBe(true);
    expect(record.finalizationReason).toBe("completed");
    expect(record.reportGeneratedAt).toBe("2026-04-01T00:10:00.000Z");
    expect(typeof record.score).toBe("number");
    expect(record.score).toBeGreaterThan(0);
  });
});
