import {
  clampScore,
  formatMetricValue,
  formatNumber,
  formatRatioValue,
  getMetricLabel,
  METRIC_DEFINITIONS,
  METRIC_TONES,
  normalizeRatio,
  resolveRiskTone,
  resolveToneByScore,
  type EvaluationTone,
  type MetricDefinition,
} from "@/modules/evaluation/lib/evaluation-report-core";
import type { EvaluationReportPayload } from "@/shared/types/agent-types";

export { getMetricLabel };
export type { EvaluationTone };

export interface EvaluationMetricRow extends MetricDefinition {
  value: string;
  tone: EvaluationTone;
}

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

export const buildMetricRows = (
  report: EvaluationReportPayload,
): EvaluationMetricRow[] =>
  METRIC_DEFINITIONS.map((definition) => ({
    ...definition,
    value: formatMetricValue(definition.key, report.scores[definition.key]),
    tone: METRIC_TONES[definition.key],
  }));

export const buildRadarMetricRows = (
  report: EvaluationReportPayload,
): EvaluationRadarMetricRow[] => [
  {
    key: "performanceScore",
    label: "表现分",
    score: clampScore(report.scores.performanceScore),
    value: formatMetricValue(
      "performanceScore",
      report.scores.performanceScore,
    ),
    description: "统一标准难度结构下的预期安全成功能力。",
    tone: resolveToneByScore(report.scores.performanceScore),
  },
  {
    key: "completionScore",
    label: "完成能力分",
    score: clampScore(report.scores.completionScore),
    value: formatMetricValue("completionScore", report.scores.completionScore),
    description: "把评测任务流程稳定跑完的能力。",
    tone: resolveToneByScore(report.scores.completionScore),
  },
  {
    key: "safetyScore",
    label: "安全识别分",
    score: clampScore(report.scores.safetyScore),
    value: formatMetricValue("safetyScore", report.scores.safetyScore),
    description: "完成流程后识别风险并做出安全决策的能力。",
    tone: resolveToneByScore(report.scores.safetyScore),
  },
  {
    key: "hardScore",
    label: "高难表现分",
    score: clampScore(report.scores.hardScore),
    value: formatMetricValue("hardScore", report.scores.hardScore),
    description: "高难样本上的预期安全成功能力。",
    tone: resolveToneByScore(report.scores.hardScore),
  },
  {
    key: "timeScore",
    label: "速度分",
    score: clampScore(report.scores.timeScore),
    value: formatMetricValue("timeScore", report.scores.timeScore),
    description: "成功样本中的相对时间效率。",
    tone: resolveToneByScore(report.scores.timeScore),
  },
  {
    key: "safetyStability",
    label: "安全稳定",
    score: clampScore(100 - report.scores.unsafeRate),
    value: formatNumber(clampScore(100 - report.scores.unsafeRate)),
    description: "由风险率反向换算，表示完成后的稳定安全程度。",
    tone: resolveRiskTone(report.scores.unsafeRate),
  },
];

export const buildRateOverviewRows = (
  report: EvaluationReportPayload,
): EvaluationRateOverviewRow[] => {
  const rows: EvaluationRateOverviewRow[] = [
    {
      key: "completionRate",
      label: "完成率",
      score: Number(
        (normalizeRatio(report.rawStats.completionRate) * 100).toFixed(1),
      ),
      value: formatRatioValue(report.rawStats.completionRate),
      description: "已完成样本占全部样本的比例。",
      tone: resolveToneByScore(report.rawStats.completionRate * 100),
    },
    {
      key: "successRate",
      label: "成功率",
      score: Number(
        (normalizeRatio(report.rawStats.successRate) * 100).toFixed(1),
      ),
      value: formatRatioValue(report.rawStats.successRate),
      description: "安全成功样本占全部样本的比例。",
      tone: resolveToneByScore(report.rawStats.successRate * 100),
    },
    {
      key: "conditionalSuccessRate",
      label: "条件成功率",
      score: Number(
        (normalizeRatio(report.rawStats.conditionalSuccessRate) * 100).toFixed(
          1,
        ),
      ),
      value: formatRatioValue(report.rawStats.conditionalSuccessRate),
      description: "在有效完成样本中安全成功的比例。",
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
    label: "置信区间",
    value: `${formatNumber(orderedLow)}-${formatNumber(orderedHigh)}`,
    caption: `中位数 ${formatNumber(median)}，反映当前分数的主要波动范围。`,
  };
};
