import { describe, expect, it } from "vitest";
import type { EvaluationRecord } from "../../../shared/types/AgentTypes";
import { filterEvaluationRecords, shouldPollEvaluation } from "./index";

const records: EvaluationRecord[] = [
  {
    evaluationId: "eval-running",
    agentName: "Sentinel",
    createdAt: "2025-05-01T08:00:00Z",
    updatedAt: "2025-05-01T08:05:00Z",
    status: "running",
    progressPercent: 45,
    finalReportAvailable: false,
    finalizationReason: null,
    publicToLeaderboard: false,
    datasetIds: ["A1"],
    datasetNames: ["Identity leak"],
    submitMethod: "api",
    score: null,
    ownerName: "Alice",
    parameters: {
      difficulty: 3,
      timeoutMinutes: 20,
      retryEnabled: true,
    },
  },
  {
    evaluationId: "eval-completed",
    agentName: "Boundary Guard",
    createdAt: "2025-05-02T08:00:00Z",
    updatedAt: "2025-05-02T08:10:00Z",
    status: "completed",
    progressPercent: 100,
    finalReportAvailable: true,
    finalizationReason: "completed",
    publicToLeaderboard: true,
    datasetIds: ["B1"],
    datasetNames: ["Command injection"],
    submitMethod: "docker",
    score: 91.4,
    ownerName: "Bob",
    parameters: {
      difficulty: 4,
      timeoutMinutes: 25,
      retryEnabled: false,
    },
  },
];

describe("evaluation filters", () => {
  it("applies status, visibility, submit method and search filters", () => {
    const result = filterEvaluationRecords(records, {
      status: "completed",
      visibility: "public",
      submitMethod: "docker",
      search: "Boundary",
    });

    expect(result.map((item) => item.evaluationId)).toEqual(["eval-completed"]);
  });

  it("stops polling paused and terminal states", () => {
    expect(shouldPollEvaluation("running")).toBe(true);
    expect(shouldPollEvaluation("pending")).toBe(true);
    expect(shouldPollEvaluation("paused")).toBe(false);
    expect(shouldPollEvaluation("completed")).toBe(false);
  });
});
