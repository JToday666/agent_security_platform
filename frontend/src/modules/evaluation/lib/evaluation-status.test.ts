import { describe, expect, it, vi } from "vitest";
import type { EvaluationRecord } from "@/shared/types/agent-types";
import {
  EVALUATION_STATUS_OPTIONS,
  getEvaluationStatusFilterOptions,
  getEvaluationStatusIcon,
  getEvaluationStatusTagTone,
  shouldPollEvaluation,
} from "@/modules/evaluation/lib/evaluation-status";
import {
  filterEvaluationRecords,
  type EvaluationRecordFilters,
} from "@/modules/evaluation/lib/evaluation-record-filters";

const createRecord = (
  status: EvaluationRecord["status"],
): EvaluationRecord => ({
  evaluationId: `eval-${status}`,
  agentName: "Agent",
  createdAt: "2026-05-01T00:00:00.000Z",
  updatedAt: "2026-05-01T00:00:00.000Z",
  status,
  progressPercent: 0,
  finalReportAvailable: false,
  finalizationReason: null,
  publicToLeaderboard: true,
  leaderboardDisplayMode: "public",
  datasetIds: ["dataset-1"],
  datasetNames: ["Dataset"],
  submitMethod: "api",
  score: null,
  ownerName: "Owner",
  parameters: {
    difficulty: 0.5,
    timeoutMinutes: 10,
    maxSteps: 5,
  },
});

const baseFilters: EvaluationRecordFilters = {
  status: "all",
  visibility: "all",
  submitMethod: "all",
  search: "",
};

describe("evaluation status helpers", () => {
  it("exposes every evaluation status as a filter option", () => {
    const t = vi.fn((key: string) => `translated:${key}`);

    const options = getEvaluationStatusFilterOptions(t);

    expect(options.map((option) => option.value)).toEqual(
      EVALUATION_STATUS_OPTIONS,
    );
    expect(options[0]).toEqual({
      label: "translated:evaluation.status.queued",
      value: "queued",
    });
    expect(t).toHaveBeenCalledTimes(EVALUATION_STATUS_OPTIONS.length);
  });

  it("filters records for every individual evaluation status", () => {
    const records = EVALUATION_STATUS_OPTIONS.map(createRecord);

    for (const status of EVALUATION_STATUS_OPTIONS) {
      expect(
        filterEvaluationRecords(records, {
          ...baseFilters,
          status,
        }).map((record) => record.status),
      ).toEqual([status]);
    }
  });

  it("does not render intermediate statuses as failed", () => {
    expect(getEvaluationStatusIcon("queued")).toBe("app:status.queued");
    expect(getEvaluationStatusIcon("pausing")).toBe("app:status.paused");
    expect(getEvaluationStatusIcon("terminating")).toBe(
      "app:status.terminated",
    );
    expect(getEvaluationStatusIcon("canceling")).toBe("app:status.canceled");

    expect(getEvaluationStatusTagTone("queued")).toBe("warning");
    expect(getEvaluationStatusTagTone("pausing")).toBe("warning");
    expect(getEvaluationStatusTagTone("terminating")).toBe("warning");
    expect(getEvaluationStatusTagTone("canceling")).toBe("info");
  });

  it("polls only non-terminal active statuses", () => {
    expect(shouldPollEvaluation("paused")).toBe(false);
    expect(shouldPollEvaluation("completed")).toBe(false);
    expect(shouldPollEvaluation("terminated")).toBe(false);
    expect(shouldPollEvaluation("canceled")).toBe(false);
    expect(shouldPollEvaluation("failed")).toBe(false);
    expect(shouldPollEvaluation("canceling")).toBe(true);
  });
});
