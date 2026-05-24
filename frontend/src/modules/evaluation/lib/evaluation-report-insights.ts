import {
  formatMetricValue,
  formatNumber,
  formatPercentValue,
  resolveRiskTone,
  resolveToneByScore,
  type EvaluationTone,
} from "@/modules/evaluation/lib/evaluation-report-core";
import {
  type AppTranslator,
  translateRuntimeMessage,
} from "@/app/i18n/runtime-translator";
import type {
  EvaluationReportPayload,
  EvaluationScoreTrend,
  EvaluationScoreTrendView,
} from "@/shared/types/agent-types";

export interface EvaluationReportHighlight {
  label: string;
  value: string;
  caption: string;
  tone: EvaluationTone;
}

export interface EvaluationReportInsight {
  title: string;
  value: string;
  caption: string;
  tone: EvaluationTone;
}

export interface EvaluationSelectableInsight extends EvaluationReportInsight {
  key: string;
}

export interface EvaluationTrendSummary {
  latestLabel: string;
  latestValue: string;
  deltaLabel: string;
  deltaValue: string;
  deltaTone: EvaluationTone;
  sampleLabel: string;
  sampleValue: string;
}

export const buildTrendSummary = (
  trend: EvaluationScoreTrend | null,
  view: EvaluationScoreTrendView,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationTrendSummary => {
  const items = trend?.items ?? [];
  const latest = items[items.length - 1];
  const previous = items[items.length - 2];
  const metricKey =
    trend?.views[view]?.metrics[0] ??
    (view === "risk" ? "unsafeRate" : "conservativeScore");
  const latestValue = latest?.scores[metricKey] ?? 0;
  const previousValue = previous?.scores[metricKey] ?? latestValue;
  const delta = Number((latestValue - previousValue).toFixed(1));
  const trendImproved = metricKey === "unsafeRate" ? delta <= 0 : delta >= 0;

  return {
    latestLabel:
      metricKey === "unsafeRate"
        ? t("evaluation.trend.latestRiskRate")
        : t("evaluation.trend.latestCompositeScore"),
    latestValue: formatMetricValue(metricKey, latestValue),
    deltaLabel: t("evaluation.trend.delta"),
    deltaValue:
      delta === 0
        ? t("evaluation.trend.flat")
        : `${delta > 0 ? "+" : ""}${formatMetricValue(metricKey, delta)}`,
    deltaTone: delta === 0 ? "neutral" : trendImproved ? "success" : "danger",
    sampleLabel: t("evaluation.trend.sampleCount"),
    sampleValue: t("evaluation.common.countRecords", { count: items.length }),
  };
};

export const buildReportHighlights = (
  report: EvaluationReportPayload,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationReportHighlight[] => [
  {
    label: t("evaluation.metrics.conservativeScore.label"),
    value: formatMetricValue(
      "conservativeScore",
      report.scores.conservativeScore,
    ),
    caption: t("evaluation.report.highlightScoreCaption"),
    tone: resolveToneByScore(report.scores.conservativeScore),
  },
  {
    label: t("evaluation.report.highlightSafetyLabel"),
    value: formatMetricValue("safetyScore", report.scores.safetyScore),
    caption: t("evaluation.report.highlightSafetyCaption"),
    tone: resolveToneByScore(report.scores.safetyScore),
  },
  {
    label: t("evaluation.metrics.unsafeRate.label"),
    value: formatMetricValue("unsafeRate", report.scores.unsafeRate),
    caption: t("evaluation.report.highlightRiskCaption"),
    tone: resolveRiskTone(report.scores.unsafeRate),
  },
  {
    label: t("evaluation.metrics.confidenceInterval.label"),
    value: `${formatNumber(report.posteriorInterval.psQ05)}-${formatNumber(
      report.posteriorInterval.psQ95,
    )}`,
    caption: t("evaluation.report.highlightConfidenceCaption"),
    tone: "primary",
  },
];

export const resolveDifficultyBucketInsight = (
  report: EvaluationReportPayload,
  selectedBucket: string | null,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationSelectableInsight => {
  const buckets = report.breakdowns.difficultyBuckets;
  const selected = selectedBucket
    ? buckets.find((item) => item.bucket === selectedBucket)
    : null;
  const weakest = buckets.length
    ? buckets.reduce((current, item) =>
        item.successRate < current.successRate ? item : current,
      )
    : null;
  const bucket = selected ?? weakest;

  if (!bucket) {
    return {
      key: "",
      title: t("evaluation.report.difficultyInsightTitle"),
      value: t("evaluation.common.noReturn"),
      caption: t("evaluation.report.difficultyInsightEmpty"),
      tone: "neutral",
    };
  }

  return {
    key: bucket.bucket,
    title: t("evaluation.report.difficultyInsightTitle"),
    value: bucket.bucket,
    caption: t("evaluation.report.difficultyOutcomeCaption", {
      rate: formatPercentValue(bucket.successRate),
      success: bucket.success,
      failed: bucket.failed,
      error: bucket.error,
    }),
    tone:
      bucket.successRate < 0.45
        ? "danger"
        : bucket.successRate < 0.65
          ? "warning"
          : "primary",
  };
};

export const resolveDatasetSummaryInsight = (
  report: EvaluationReportPayload,
  selectedDatasetId: string | null,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationSelectableInsight => {
  const datasets = report.breakdowns.datasetSummaries;
  const selected = selectedDatasetId
    ? datasets.find((item) => item.datasetId === selectedDatasetId)
    : null;
  const riskiest = datasets.length
    ? datasets.reduce((current, item) => {
        const currentRisk = current.failed + current.error;
        const nextRisk = item.failed + item.error;
        return nextRisk > currentRisk ? item : current;
      })
    : null;
  const dataset = selected ?? riskiest;

  if (!dataset) {
    return {
      key: "",
      title: t("evaluation.report.datasetInsightTitle"),
      value: t("evaluation.common.noReturn"),
      caption: t("evaluation.report.datasetInsightEmpty"),
      tone: "neutral",
    };
  }

  const riskCount = dataset.failed + dataset.error;

  return {
    key: dataset.datasetId,
    title: t("evaluation.report.datasetInsightTitle"),
    value: dataset.datasetName,
    caption: t("evaluation.report.outcomeCaption", {
      success: dataset.success,
      failed: dataset.failed,
      error: dataset.error,
    }),
    tone: riskCount > 0 ? "warning" : "success",
  };
};

const resolveSampleLocationInsight = (
  report: EvaluationReportPayload,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationReportInsight => {
  const points = report.breakdowns.sampleScatterPoints;
  const slowestPoint = points.length
    ? points.reduce((current, item) =>
        item.durationMs > current.durationMs ? item : current,
      )
    : null;

  if (!slowestPoint) {
    return {
      title: t("evaluation.report.sampleLocationTitle"),
      value: t("evaluation.common.noReturn"),
      caption: t("evaluation.report.sampleLocationEmpty"),
      tone: "neutral",
    };
  }

  const riskPoints = points.filter(
    (item) =>
      item.normalizedResult === "failed" || item.normalizedResult === "error",
  );
  const sortedDurations = points
    .map((item) => item.durationMs)
    .sort((left, right) => left - right);
  const durationIndex = Math.max(
    0,
    Math.ceil(sortedDurations.length * 0.75) - 1,
  );
  const highDurationThreshold = sortedDurations[durationIndex] ?? 0;
  const highDifficultyRiskCount = riskPoints.filter(
    (item) => item.difficulty >= 0.7,
  ).length;
  const highDurationRiskCount = riskPoints.filter(
    (item) => item.durationMs >= highDurationThreshold,
  ).length;

  return {
    title: t("evaluation.report.sampleLocationTitle"),
    value: `${Math.round(slowestPoint.durationMs / 1000)}s`,
    caption: riskPoints.length
      ? t("evaluation.report.sampleLocationRiskCaption", {
          riskCount: riskPoints.length,
          highDifficultyCount: highDifficultyRiskCount,
          highDurationCount: highDurationRiskCount,
        })
      : t("evaluation.report.sampleLocationSafeCaption", {
          sampleId: slowestPoint.sampleId,
        }),
    tone: riskPoints.length ? "warning" : "neutral",
  };
};

export const buildReportInsights = (
  report: EvaluationReportPayload,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationReportInsight[] => {
  const outcome = report.breakdowns.outcomeSummary;
  const total = Math.max(1, outcome.success + outcome.failed + outcome.error);
  const successRate = outcome.success / total;

  return [
    {
      title: t("evaluation.report.abilitySection"),
      value: formatMetricValue(
        "performanceScore",
        report.scores.performanceScore,
      ),
      caption: t("evaluation.report.structureCaption"),
      tone: resolveToneByScore(report.scores.performanceScore),
    },
    {
      title: t("evaluation.report.outcomeSection"),
      value: formatPercentValue(successRate),
      caption: t("evaluation.report.outcomeCaption", {
        success: outcome.success,
        failed: outcome.failed,
        error: outcome.error,
      }),
      tone: resolveToneByScore(successRate * 100),
    },
    resolveDifficultyBucketInsight(report, null, t),
    resolveDatasetSummaryInsight(report, null, t),
    resolveSampleLocationInsight(report, t),
  ];
};
