import {
  clampScore,
  formatMetricValue,
  formatNumber,
  formatRatioValue,
  getMetricLabel,
  normalizeRatio,
  resolveRiskTone,
  resolveToneByScore,
  type EvaluationTone,
} from "@/modules/evaluation/lib/evaluation-report-core";
import {
  type AppTranslator,
  translateRuntimeMessage,
} from "@/app/i18n/runtime-translator";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";

export { getMetricLabel };
export type { EvaluationTone };

export interface EvaluationRadarMetricRow {
  key: string;
  label: string;
  score: number;
  value: string;
  description: string;
  tone: EvaluationTone;
}

export interface EvaluationRateOverviewRow {
  key: string;
  label: string;
  value: string;
  score: number;
  description: string;
  tone: EvaluationTone;
}

export interface EvaluationConfidenceSummary {
  low: number;
  median: number;
  high: number;
  label: string;
  value: string;
  caption: string;
}

export const buildRadarMetricRows = (
  report: EvaluationReportPayload,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationRadarMetricRow[] => [
  {
    key: "performanceScore",
    label: t("evaluation.metrics.performanceScore.label"),
    score: clampScore(report.scores.performanceScore),
    value: formatMetricValue(
      "performanceScore",
      report.scores.performanceScore,
    ),
    description: t("evaluation.metrics.performanceScore.radarDescription"),
    tone: resolveToneByScore(report.scores.performanceScore),
  },
  {
    key: "completionScore",
    label: t("evaluation.metrics.completionScore.label"),
    score: clampScore(report.scores.completionScore),
    value: formatMetricValue("completionScore", report.scores.completionScore),
    description: t("evaluation.metrics.completionScore.radarDescription"),
    tone: resolveToneByScore(report.scores.completionScore),
  },
  {
    key: "safetyScore",
    label: t("evaluation.metrics.safetyScore.label"),
    score: clampScore(report.scores.safetyScore),
    value: formatMetricValue("safetyScore", report.scores.safetyScore),
    description: t("evaluation.metrics.safetyScore.radarDescription"),
    tone: resolveToneByScore(report.scores.safetyScore),
  },
  {
    key: "hardScore",
    label: t("evaluation.metrics.hardScore.label"),
    score: clampScore(report.scores.hardScore),
    value: formatMetricValue("hardScore", report.scores.hardScore),
    description: t("evaluation.metrics.hardScore.description"),
    tone: resolveToneByScore(report.scores.hardScore),
  },
  {
    key: "timeScore",
    label: t("evaluation.metrics.timeScore.label"),
    score: clampScore(report.scores.timeScore),
    value: formatMetricValue("timeScore", report.scores.timeScore),
    description: t("evaluation.metrics.timeScore.description"),
    tone: resolveToneByScore(report.scores.timeScore),
  },
  {
    key: "safetyStability",
    label: t("evaluation.metrics.safetyStability.label"),
    score: clampScore(100 - report.scores.unsafeRate),
    value: formatNumber(clampScore(100 - report.scores.unsafeRate)),
    description: t("evaluation.metrics.safetyStability.description"),
    tone: resolveRiskTone(report.scores.unsafeRate),
  },
];

export const buildRateOverviewRows = (
  report: EvaluationReportPayload,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationRateOverviewRow[] => {
  const rows: EvaluationRateOverviewRow[] = [
    {
      key: "completionRate",
      label: t("evaluation.metrics.completionRate.label"),
      score: Number(
        (normalizeRatio(report.rawStats.completionRate) * 100).toFixed(1),
      ),
      value: formatRatioValue(report.rawStats.completionRate),
      description: t("evaluation.metrics.completionRate.description"),
      tone: resolveToneByScore(report.rawStats.completionRate * 100),
    },
    {
      key: "successRate",
      label: t("evaluation.metrics.successRate.label"),
      score: Number(
        (normalizeRatio(report.rawStats.successRate) * 100).toFixed(1),
      ),
      value: formatRatioValue(report.rawStats.successRate),
      description: t("evaluation.metrics.successRate.description"),
      tone: resolveToneByScore(report.rawStats.successRate * 100),
    },
    {
      key: "conditionalSuccessRate",
      label: t("evaluation.metrics.conditionalSuccessRate.label"),
      score: Number(
        (normalizeRatio(report.rawStats.conditionalSuccessRate) * 100).toFixed(
          1,
        ),
      ),
      value: formatRatioValue(report.rawStats.conditionalSuccessRate),
      description: t("evaluation.metrics.conditionalSuccessRate.description"),
      tone: resolveToneByScore(report.rawStats.conditionalSuccessRate * 100),
    },
  ];

  const hasStats =
    report.rawStats.total > 0 ||
    rows.some((row) => row.score > 0 && Number.isFinite(row.score));

  return hasStats ? rows : [];
};

export const buildConfidenceSummary = (
  report: EvaluationReportPayload,
  t: AppTranslator = translateRuntimeMessage,
): EvaluationConfidenceSummary => {
  const low = clampScore(report.posteriorInterval.psQ05);
  const high = clampScore(report.posteriorInterval.psQ95);
  const orderedLow = Math.min(low, high);
  const orderedHigh = Math.max(low, high);
  const median = Math.min(
    orderedHigh,
    Math.max(orderedLow, clampScore(report.posteriorInterval.psQ50)),
  );

  return {
    low: orderedLow,
    median,
    high: orderedHigh,
    label: t("evaluation.metrics.confidenceInterval.label"),
    value: `${formatNumber(orderedLow)}-${formatNumber(orderedHigh)}`,
    caption: t("evaluation.metrics.confidenceInterval.caption", {
      median: formatNumber(median),
    }),
  };
};
