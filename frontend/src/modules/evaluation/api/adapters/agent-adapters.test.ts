import { describe, expect, it } from "vitest";
import {
  adaptEvaluationDetail,
  adaptEvaluationRecord,
  adaptSubmitMeta,
} from "./agent-adapters";
import { normalizeMaxSteps } from "@/modules/submission/model/parameter-validator";

describe("adaptSubmitMeta", () => {
  it("defaults maxSteps step to 1 when the backend omits it", () => {
    const meta = adaptSubmitMeta({
      supportedMethods: ["api"],
      difficulty: { min: 0, max: 1, step: 0.1, default: 0.5 },
      timeoutMinutes: { min: 15, max: 30, step: 1, default: 15 },
      maxSteps: { min: 1, max: 100, default: 30 },
      leaderboardDisplayMode: {
        default: "public",
        options: ["public", "anonymous"],
      },
    });

    expect(meta.maxSteps.step).toBe(1);
    expect(normalizeMaxSteps(42, meta.maxSteps)).toBe(42);
  });

  it("treats a zero step as a unit step fallback", () => {
    const meta = adaptSubmitMeta({
      supportedMethods: ["api"],
      difficulty: { min: 0, max: 1, step: 0.1, default: 0.5 },
      timeoutMinutes: { min: 15, max: 30, step: 1, default: 15 },
      maxSteps: { min: 1, max: 100, step: 0, default: 30 },
      leaderboardDisplayMode: {
        default: "public",
        options: ["public", "anonymous"],
      },
    });

    expect(meta.maxSteps.step).toBe(1);
    expect(Number.isFinite(normalizeMaxSteps(42, meta.maxSteps))).toBe(true);
  });
});

describe("evaluation detail adapters", () => {
  it("keeps numeric scores returned by the backend", () => {
    const record = adaptEvaluationRecord({
      evaluationId: "eval_1",
      agentName: "demo",
      createdAt: "2026-05-24T10:00:00Z",
      updatedAt: "2026-05-24T10:05:00Z",
      status: "completed",
      progressPercent: 100,
      finalReportAvailable: true,
      publicToLeaderboard: true,
      leaderboardDisplayMode: "public",
      datasetIds: ["A1_identity_leakage"],
      datasetNames: ["Identity Leakage"],
      submitMethod: "api",
      score: 87.6,
      ownerName: "owner",
      parameters: {
        difficulty: 0.5,
        timeoutMinutes: 15,
        maxSteps: 30,
      },
    });

    expect(record.score).toBe(87.6);
  });

  it("adapts backend runtime timestamps and sample counts", () => {
    const detail = adaptEvaluationDetail({
      evaluationId: "eval_1",
      agentName: "demo",
      createdAt: "2026-05-24T10:00:00Z",
      updatedAt: "2026-05-24T10:05:00Z",
      startedAt: "2026-05-24T10:01:00Z",
      finishedAt: "2026-05-24T10:04:00Z",
      status: "completed",
      progressPercent: 100,
      finalReportAvailable: true,
      publicToLeaderboard: true,
      leaderboardDisplayMode: "public",
      datasetIds: ["A1_identity_leakage"],
      datasetNames: ["Identity Leakage"],
      submitMethod: "api",
      score: 91.2,
      ownerName: "owner",
      parameters: {
        difficulty: 0.5,
        timeoutMinutes: 15,
        maxSteps: 30,
      },
      progress: {
        percent: 100,
        totalDatasetCount: 1,
        completedDatasetCount: 1,
        totalSampleCount: 12,
        completedSampleCount: 12,
        statusText: "评测已完成。",
      },
    });

    expect(detail.startedAt).toBe("2026-05-24T10:01:00Z");
    expect(detail.finishedAt).toBe("2026-05-24T10:04:00Z");
    expect(detail.progress.totalSampleCount).toBe(12);
    expect(detail.progress.completedSampleCount).toBe(12);
  });
});
