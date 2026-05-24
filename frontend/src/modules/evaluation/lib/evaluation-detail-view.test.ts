import { describe, expect, it } from "vitest";
import {
  buildEvaluationSampleBase,
  formatEvaluationPrimaryScore,
} from "@/modules/evaluation/lib/evaluation-detail-view";
import type {
  EvaluationDetail,
  EvaluationReportPayload,
} from "@/shared/types/agent-types";

const createDetail = (
  overrides: Partial<EvaluationDetail> = {},
): EvaluationDetail => ({
  evaluationId: "eval_1",
  agentName: "demo",
  createdAt: "2026-05-24T10:00:00Z",
  updatedAt: "2026-05-24T10:05:00Z",
  startedAt: "2026-05-24T10:01:00Z",
  finishedAt: "2026-05-24T10:04:00Z",
  status: "completed",
  finalReportAvailable: true,
  finalizationReason: "completed",
  publicToLeaderboard: true,
  leaderboardDisplayMode: "public",
  datasetIds: ["A1_identity_leakage"],
  datasetNames: ["Identity Leakage"],
  submitMethod: "api",
  score: null,
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
    runningDatasetId: null,
    runningDatasetName: null,
    pauseDeadlineAt: null,
    statusText: "评测已完成。",
  },
  controls: {
    canPause: false,
    canResume: false,
    canTerminate: false,
    canCancel: false,
    pauseUsed: false,
  },
  report: null,
  sampleSummary: null,
  representativeSamples: {
    success: null,
    failed: null,
    error: null,
  },
  downloads: {
    sampleDetailsUrl: null,
  },
  ...overrides,
});

const createReport = (
  overrides: Partial<EvaluationReportPayload> = {},
): EvaluationReportPayload => ({
  evaluationId: "eval_1",
  status: "ready",
  generatedAt: "2026-05-24T10:05:00Z",
  scores: {
    conservativeScore: 87.4,
    performanceScore: 90,
    confidence: 80,
    completionScore: 100,
    safetyScore: 92,
    hardScore: 76,
    unsafeRate: 8,
    timeScore: 85,
  },
  rawStats: {
    total: 12,
    success: 9,
    failed: 2,
    error: 1,
    completionRate: 1,
    successRate: 0.75,
    conditionalSuccessRate: 0.82,
  },
  posteriorInterval: {
    psQ05: 82,
    psQ50: 87.4,
    psQ95: 91,
  },
  coverage: {
    difficultyBucketHitCount: 3,
    difficultyCoverageRatio: 0.6,
  },
  breakdowns: {
    outcomeSummary: {
      total: 12,
      success: 9,
      failed: 2,
      error: 1,
    },
    difficultyBuckets: [],
    datasetSummaries: [],
    sampleScatterPoints: [],
  },
  versions: {
    difficultyVersion: "legacy_current",
    scoreModelVersion: "score_v1_5",
    benchmarkVersion: "bm_v1",
  },
  ...overrides,
});

describe("evaluation detail view", () => {
  it("uses report score when detail score is temporarily missing", () => {
    const detail = createDetail({ score: null });
    const report = createReport();
    const formatScore = formatEvaluationPrimaryScore as (
      detail: EvaluationDetail,
      report: EvaluationReportPayload | null,
    ) => string;

    expect(formatScore(detail, report)).toBe("87.4");
  });

  it("uses report raw stats for sample outcome totals", () => {
    const detail = createDetail({
      sampleSummary: null,
      progress: {
        ...createDetail().progress,
        totalSampleCount: 0,
        completedSampleCount: 0,
      },
    });
    const report = createReport();
    const buildSampleBase = buildEvaluationSampleBase as (
      detail: EvaluationDetail,
      report: EvaluationReportPayload | null,
    ) => ReturnType<typeof buildEvaluationSampleBase>;

    expect(buildSampleBase(detail, report)).toEqual({
      total: 12,
      success: 9,
      failed: 2,
      error: 1,
      completed: 12,
    });
  });
});
