import { describe, expect, it } from "vitest";
import { buildEvaluationTrendFromRecords } from "@/modules/evaluation/lib/evaluation-record-trend";
import type { EvaluationRecord } from "@/shared/types/agent-types";

const createRecord = (
  index: number,
  score: number | null,
): EvaluationRecord => ({
  evaluationId: `eval_${index}`,
  agentName: `agent ${index}`,
  createdAt: `2026-05-${String(index).padStart(2, "0")}T10:00:00Z`,
  updatedAt: `2026-05-${String(index).padStart(2, "0")}T10:05:00Z`,
  finishedAt: `2026-05-${String(index).padStart(2, "0")}T10:04:00Z`,
  status: "completed",
  progressPercent: 100,
  finalReportAvailable: score !== null,
  finalizationReason: "completed",
  publicToLeaderboard: true,
  leaderboardDisplayMode: "public",
  datasetIds: ["A1_identity_leakage"],
  datasetNames: ["Identity Leakage"],
  submitMethod: "api",
  score,
  ownerName: "owner",
  parameters: {
    difficulty: 0.5,
    timeoutMinutes: 15,
    maxSteps: 30,
  },
});

describe("buildEvaluationTrendFromRecords", () => {
  it("derives recent trend items from completed records with scores", () => {
    const records = [
      createRecord(1, 81.2),
      createRecord(2, null),
      createRecord(3, 86.7),
    ];

    const trend = buildEvaluationTrendFromRecords(records, "recent10");

    expect(trend.items.map((item) => item.evaluationId)).toEqual([
      "eval_1",
      "eval_3",
    ]);
    expect(trend.items[1].scores.conservativeScore).toBe(86.7);
  });
});
