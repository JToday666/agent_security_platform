import { normalizeApiAssetUrl } from "@/shared/api/api-runtime";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import type {
  EvaluationDownloads,
  EvaluationRepresentativeSample,
  EvaluationRepresentativeSamples,
  EvaluationReportPayload,
  EvaluationReportScores,
  EvaluationSampleOutcome,
  EvaluationSampleSummary,
  EvaluationScoreMetricKey,
  EvaluationScoreTrend,
  EvaluationScoreTrendScope,
  EvaluationScoreTrendView,
} from "@/shared/types/agent-types";

type UnknownRecord = Record<string, unknown>;

const SCORE_KEYS: EvaluationScoreMetricKey[] = [
  "conservativeScore",
  "performanceScore",
  "confidence",
  "completionScore",
  "safetyScore",
  "hardScore",
  "unsafeRate",
  "timeScore",
];

const toRecord = (value: unknown): UnknownRecord =>
  value && typeof value === "object" ? (value as UnknownRecord) : {};

const toStringValue = (value: unknown): string =>
  typeof value === "string" ? value.trim() : "";

const toOptionalString = (value: unknown): string | null => {
  const normalized = toStringValue(value);
  return normalized ? normalized : null;
};

const toNumberValue = (value: unknown, fallback = 0): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const toScoreValue = (value: unknown): number =>
  Number(toNumberValue(value, 0).toFixed(1));

const toOutcome = (value: unknown): EvaluationSampleOutcome => {
  const normalized = toStringValue(value);
  if (normalized === "failed" || normalized === "error") {
    return normalized;
  }
  return "success";
};

export const normalizeEvaluationSampleSummary = (
  value: unknown,
): EvaluationSampleSummary | null => {
  if (!value || typeof value !== "object") {
    return null;
  }

  const candidate = value as UnknownRecord;
  return {
    total: Math.max(0, Math.round(toNumberValue(candidate.total, 0))),
    success: Math.max(0, Math.round(toNumberValue(candidate.success, 0))),
    failed: Math.max(0, Math.round(toNumberValue(candidate.failed, 0))),
    error: Math.max(0, Math.round(toNumberValue(candidate.error, 0))),
  };
};

const normalizeRepresentativeSample = (
  value: unknown,
): EvaluationRepresentativeSample | null => {
  if (!value || typeof value !== "object") {
    return null;
  }

  const candidate = value as UnknownRecord;
  const sampleId = toStringValue(candidate.sampleId);
  if (!sampleId) {
    return null;
  }

  return {
    sampleId,
    datasetName:
      toStringValue(candidate.datasetName) ||
      translateRuntimeMessage("evaluation.common.unnamedDataset"),
    normalizedResult: toOutcome(candidate.normalizedResult),
    outcomeReasonText: toStringValue(candidate.outcomeReasonText),
    replayUrl: normalizeApiAssetUrl(toOptionalString(candidate.replayUrl)),
  };
};

export const normalizeRepresentativeSamples = (
  value: unknown,
): EvaluationRepresentativeSamples => {
  const candidate = toRecord(value);
  return {
    success: normalizeRepresentativeSample(candidate.success),
    failed: normalizeRepresentativeSample(candidate.failed),
    error: normalizeRepresentativeSample(candidate.error),
  };
};

export const normalizeEvaluationDownloads = (
  value: unknown,
): EvaluationDownloads => {
  const candidate = toRecord(value);
  return {
    sampleDetailsUrl: normalizeApiAssetUrl(
      toOptionalString(candidate.sampleDetailsUrl),
    ),
  };
};

const normalizeScope = (value: unknown): EvaluationScoreTrendScope =>
  toStringValue(value) === "all" ? "all" : "recent10";

const normalizeView = (value: unknown): EvaluationScoreTrendView =>
  toStringValue(value) === "risk" ? "risk" : "capability";

const normalizeMetricKeys = (
  value: unknown,
  fallback: EvaluationScoreMetricKey[],
): EvaluationScoreMetricKey[] => {
  if (!Array.isArray(value)) {
    return fallback;
  }

  const normalized = value
    .map((item) => toStringValue(item) as EvaluationScoreMetricKey)
    .filter((item) => SCORE_KEYS.includes(item));

  return normalized.length ? normalized : fallback;
};

export const adaptEvaluationScoreTrend = (
  value: unknown,
): EvaluationScoreTrend => {
  const candidate = toRecord(value);
  const views = toRecord(candidate.views);
  const capability = toRecord(views.capability);
  const risk = toRecord(views.risk);

  return {
    scope: normalizeScope(candidate.scope),
    defaultScope: normalizeScope(candidate.defaultScope),
    defaultView: normalizeView(candidate.defaultView),
    views: {
      capability: {
        label:
          toStringValue(capability.label) ||
          translateRuntimeMessage("evaluation.trend.capabilityView"),
        metrics: normalizeMetricKeys(capability.metrics, [
          "conservativeScore",
          "performanceScore",
          "hardScore",
        ]),
      },
      risk: {
        label:
          toStringValue(risk.label) ||
          translateRuntimeMessage("evaluation.trend.riskView"),
        metrics: normalizeMetricKeys(risk.metrics, [
          "conservativeScore",
          "confidence",
          "unsafeRate",
        ]),
      },
    },
    items: Array.isArray(candidate.items)
      ? candidate.items
          .map((item) => {
            const row = toRecord(item);
            const scores = toRecord(row.scores);
            const evaluationId = toStringValue(row.evaluationId);
            if (!evaluationId) {
              return null;
            }

            return {
              evaluationId,
              agentName:
                toStringValue(row.agentName) ||
                translateRuntimeMessage("evaluation.common.unnamedAgent"),
              createdAt: toStringValue(row.createdAt),
              finishedAt: toOptionalString(row.finishedAt),
              scores: SCORE_KEYS.reduce(
                (accumulator, key) => {
                  if (scores[key] != null) {
                    accumulator[key] = toScoreValue(scores[key]);
                  }
                  return accumulator;
                },
                {} as EvaluationScoreTrend["items"][number]["scores"],
              ),
            };
          })
          .filter(
            (item): item is EvaluationScoreTrend["items"][number] =>
              item !== null,
          )
      : [],
  };
};

const normalizeScores = (value: unknown): EvaluationReportScores => {
  const candidate = toRecord(value);
  return SCORE_KEYS.reduce((accumulator, key) => {
    accumulator[key] = toScoreValue(candidate[key]);
    return accumulator;
  }, {} as EvaluationReportScores);
};

export const adaptEvaluationReportPayload = (
  value: unknown,
): EvaluationReportPayload => {
  const candidate = toRecord(value);
  const rawStats = normalizeEvaluationSampleSummary(candidate.rawStats) ?? {
    total: 0,
    success: 0,
    failed: 0,
    error: 0,
  };
  const rawStatsRecord = toRecord(candidate.rawStats);
  const posteriorInterval = toRecord(candidate.posteriorInterval);
  const coverage = toRecord(candidate.coverage);
  const breakdowns = toRecord(candidate.breakdowns);
  const outcomeSummary =
    normalizeEvaluationSampleSummary(breakdowns.outcomeSummary) ?? rawStats;
  const versions = toRecord(candidate.versions);

  return {
    evaluationId: toStringValue(candidate.evaluationId),
    status: toStringValue(candidate.status) || "unavailable",
    generatedAt: toStringValue(candidate.generatedAt),
    scores: normalizeScores(candidate.scores),
    rawStats: {
      ...rawStats,
      completionRate: toNumberValue(rawStatsRecord.completionRate, 0),
      successRate: toNumberValue(rawStatsRecord.successRate, 0),
      conditionalSuccessRate: toNumberValue(
        rawStatsRecord.conditionalSuccessRate,
        0,
      ),
    },
    posteriorInterval: {
      psQ05: toScoreValue(posteriorInterval.psQ05),
      psQ50: toScoreValue(posteriorInterval.psQ50),
      psQ95: toScoreValue(posteriorInterval.psQ95),
    },
    coverage: {
      difficultyBucketHitCount: Math.max(
        0,
        Math.round(toNumberValue(coverage.difficultyBucketHitCount, 0)),
      ),
      difficultyCoverageRatio: toNumberValue(
        coverage.difficultyCoverageRatio,
        0,
      ),
    },
    breakdowns: {
      outcomeSummary,
      difficultyBuckets: Array.isArray(breakdowns.difficultyBuckets)
        ? breakdowns.difficultyBuckets.map((item) => {
            const row = toRecord(item);
            return {
              bucket: toStringValue(row.bucket),
              total: Math.max(0, Math.round(toNumberValue(row.total, 0))),
              success: Math.max(0, Math.round(toNumberValue(row.success, 0))),
              failed: Math.max(0, Math.round(toNumberValue(row.failed, 0))),
              error: Math.max(0, Math.round(toNumberValue(row.error, 0))),
              successRate: toNumberValue(row.successRate, 0),
            };
          })
        : [],
      datasetSummaries: Array.isArray(breakdowns.datasetSummaries)
        ? breakdowns.datasetSummaries.map((item) => {
            const row = toRecord(item);
            return {
              datasetId: toStringValue(row.datasetId),
              datasetName:
                toStringValue(row.datasetName) ||
                translateRuntimeMessage("evaluation.common.unnamedDataset"),
              total: Math.max(0, Math.round(toNumberValue(row.total, 0))),
              success: Math.max(0, Math.round(toNumberValue(row.success, 0))),
              failed: Math.max(0, Math.round(toNumberValue(row.failed, 0))),
              error: Math.max(0, Math.round(toNumberValue(row.error, 0))),
            };
          })
        : [],
      sampleScatterPoints: Array.isArray(breakdowns.sampleScatterPoints)
        ? breakdowns.sampleScatterPoints
            .map((item) => {
              const row = toRecord(item);
              const sampleId = toStringValue(row.sampleId);
              if (!sampleId) {
                return null;
              }
              return {
                sampleId,
                difficulty: toNumberValue(row.difficulty, 0),
                durationMs: Math.max(
                  0,
                  Math.round(toNumberValue(row.durationMs, 0)),
                ),
                normalizedResult: toOutcome(row.normalizedResult),
              };
            })
            .filter(
              (
                item,
              ): item is EvaluationReportPayload["breakdowns"]["sampleScatterPoints"][number] =>
                item !== null,
            )
        : [],
    },
    versions: {
      difficultyVersion: toStringValue(versions.difficultyVersion),
      scoreModelVersion: toStringValue(versions.scoreModelVersion),
      benchmarkVersion: toStringValue(versions.benchmarkVersion),
    },
  };
};
