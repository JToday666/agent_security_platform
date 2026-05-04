import {
  formatMetricValue,
  formatNumber,
  formatPercentValue,
  resolveRiskTone,
  resolveToneByScore,
  type EvaluationTone,
} from "@/modules/evaluation/lib/evaluation-report-core";
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
): EvaluationTrendSummary => {
  const items = trend?.items ?? [];
  const latest = items[items.length - 1];
  const previous = items[items.length - 2];
  const metricKey = view === "risk" ? "unsafeRate" : "conservativeScore";
  const latestValue = latest?.scores[metricKey] ?? 0;
  const previousValue = previous?.scores[metricKey] ?? latestValue;
  const delta = Number((latestValue - previousValue).toFixed(1));
  const trendImproved = metricKey === "unsafeRate" ? delta <= 0 : delta >= 0;

  return {
    latestLabel: view === "risk" ? "最新风险率" : "最新综合分",
    latestValue: formatMetricValue(metricKey, latestValue),
    deltaLabel: "较上一条",
    deltaValue:
      delta === 0
        ? "持平"
        : `${delta > 0 ? "+" : ""}${formatMetricValue(metricKey, delta)}`,
    deltaTone: delta === 0 ? "neutral" : trendImproved ? "success" : "danger",
    sampleLabel: "趋势样本",
    sampleValue: `${items.length} 条`,
  };
};

export const buildReportHighlights = (
  report: EvaluationReportPayload,
): EvaluationReportHighlight[] => [
  {
    label: "综合分",
    value: formatMetricValue(
      "conservativeScore",
      report.scores.conservativeScore,
    ),
    caption: "保守估计后的排行榜分数",
    tone: resolveToneByScore(report.scores.conservativeScore),
  },
  {
    label: "安全识别",
    value: formatMetricValue("safetyScore", report.scores.safetyScore),
    caption: "完成任务后的安全决策能力",
    tone: resolveToneByScore(report.scores.safetyScore),
  },
  {
    label: "风险率",
    value: formatMetricValue("unsafeRate", report.scores.unsafeRate),
    caption: "完成后出现不安全行为的比例",
    tone: resolveRiskTone(report.scores.unsafeRate),
  },
  {
    label: "置信区间",
    value: `${formatNumber(report.posteriorInterval.psQ05)}-${formatNumber(
      report.posteriorInterval.psQ95,
    )}`,
    caption: "后验分布的主要波动范围",
    tone: "primary",
  },
];

export const resolveDifficultyBucketInsight = (
  report: EvaluationReportPayload,
  selectedBucket: string | null,
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
      title: "难度桶",
      value: "未返回",
      caption: "暂无难度桶数据。",
      tone: "neutral",
    };
  }

  return {
    key: bucket.bucket,
    title: "难度桶",
    value: bucket.bucket,
    caption: `成功率 ${formatPercentValue(bucket.successRate)}。成功 ${bucket.success} 个，失败 ${bucket.failed} 个，异常 ${bucket.error} 个。`,
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
      title: "数据集结果",
      value: "未返回",
      caption: "暂无数据集结果。",
      tone: "neutral",
    };
  }

  const riskCount = dataset.failed + dataset.error;

  return {
    key: dataset.datasetId,
    title: "数据集结果",
    value: dataset.datasetName,
    caption: `成功 ${dataset.success} 个，失败 ${dataset.failed} 个，异常 ${dataset.error} 个。`,
    tone: riskCount > 0 ? "warning" : "success",
  };
};

const resolveSampleLocationInsight = (
  report: EvaluationReportPayload,
): EvaluationReportInsight => {
  const points = report.breakdowns.sampleScatterPoints;
  const slowestPoint = points.length
    ? points.reduce((current, item) =>
        item.durationMs > current.durationMs ? item : current,
      )
    : null;

  if (!slowestPoint) {
    return {
      title: "样本定位",
      value: "未返回",
      caption: "暂无散点样本。",
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
    title: "样本定位",
    value: `${Math.round(slowestPoint.durationMs / 1000)}s`,
    caption: riskPoints.length
      ? `失败/异常 ${riskPoints.length} 个，高难 ${highDifficultyRiskCount} 个，高耗时 ${highDurationRiskCount} 个。`
      : `最慢样本 ${slowestPoint.sampleId}，未发现失败或异常样本。`,
    tone: riskPoints.length ? "warning" : "neutral",
  };
};

export const buildReportInsights = (
  report: EvaluationReportPayload,
): EvaluationReportInsight[] => {
  const outcome = report.breakdowns.outcomeSummary;
  const total = Math.max(1, outcome.success + outcome.failed + outcome.error);
  const successRate = outcome.success / total;

  return [
    {
      title: "能力结构",
      value: formatMetricValue(
        "performanceScore",
        report.scores.performanceScore,
      ),
      caption: "综合完成、安全、高难和速度后的表现分。",
      tone: resolveToneByScore(report.scores.performanceScore),
    },
    {
      title: "样本结果",
      value: formatPercentValue(successRate),
      caption: `成功 ${outcome.success} 个，失败 ${outcome.failed} 个，异常 ${outcome.error} 个。`,
      tone: resolveToneByScore(successRate * 100),
    },
    resolveDifficultyBucketInsight(report, null),
    resolveDatasetSummaryInsight(report, null),
    resolveSampleLocationInsight(report),
  ];
};
