import type { EChartsOption } from "echarts";
import type {
  EvaluationRepresentativeSample,
  EvaluationRepresentativeSamples,
  EvaluationReportPayload,
  EvaluationSampleOutcome,
  EvaluationScoreMetricKey,
  EvaluationScoreTrend,
  EvaluationScoreTrendView,
} from "@/shared/types/agent-types";

interface MetricDefinition {
  key: EvaluationScoreMetricKey;
  label: string;
  description: string;
  unit?: "%";
}

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

export type EvaluationTone =
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "neutral";

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

const METRIC_DEFINITIONS: MetricDefinition[] = [
  {
    key: "conservativeScore",
    label: "综合分",
    description: "排行榜主排序分，体现平台对 Agent 能力的保守估计。",
  },
  {
    key: "performanceScore",
    label: "表现分",
    description: "在统一标准难度结构下的预期安全成功能力。",
  },
  {
    key: "confidence",
    label: "置信度",
    description: "表示当前分数受样本量、难度覆盖和不确定性影响后的可信程度。",
  },
  {
    key: "completionScore",
    label: "完成能力分",
    description: "表示 Agent 把任务流程稳定跑完的能力。",
  },
  {
    key: "safetyScore",
    label: "安全识别分",
    description: "表示 Agent 完成流程后识别陷阱并安全决策的能力。",
  },
  {
    key: "hardScore",
    label: "高难表现分",
    description: "表示高难样本上的预期安全成功能力。",
  },
  {
    key: "unsafeRate",
    label: "风险率",
    description: "表示 Agent 跑完任务但做出不安全行为的比例。",
    unit: "%",
  },
  {
    key: "timeScore",
    label: "速度分",
    description: "表示成功样本中的相对时间效率。",
  },
];

const METRIC_COLORS: Record<EvaluationScoreMetricKey, string> = {
  conservativeScore: "#2563eb",
  performanceScore: "#0f766e",
  confidence: "#7c3aed",
  completionScore: "#0891b2",
  safetyScore: "#16a34a",
  hardScore: "#ea580c",
  unsafeRate: "#dc2626",
  timeScore: "#4f46e5",
};

const OUTCOME_COLORS: Record<EvaluationSampleOutcome, string> = {
  success: "#16a34a",
  failed: "#dc2626",
  error: "#f59e0b",
};

const METRIC_TONES: Record<EvaluationScoreMetricKey, EvaluationTone> = {
  conservativeScore: "primary",
  performanceScore: "success",
  confidence: "primary",
  completionScore: "success",
  safetyScore: "success",
  hardScore: "warning",
  unsafeRate: "danger",
  timeScore: "primary",
};

export const getMetricLabel = (key: EvaluationScoreMetricKey): string =>
  METRIC_DEFINITIONS.find((item) => item.key === key)?.label ?? key;

const formatNumber = (value: number): string =>
  Number.isFinite(value) ? value.toFixed(1) : "0.0";

const clampScore = (value: number): number =>
  Number(Math.min(100, Math.max(0, Number.isFinite(value) ? value : 0)).toFixed(1));

const normalizeRatio = (value: number): number =>
  Number(Math.min(1, Math.max(0, Number.isFinite(value) ? value : 0)).toFixed(4));

const formatMetricValue = (
  key: EvaluationScoreMetricKey,
  value: number,
): string => {
  const definition = METRIC_DEFINITIONS.find((item) => item.key === key);
  return definition?.unit === "%"
    ? `${formatNumber(value)}%`
    : formatNumber(value);
};

const formatPercentValue = (value: number): string =>
  `${formatNumber(value * 100)}%`;

const formatRatioValue = (value: number): string =>
  formatPercentValue(normalizeRatio(value));

const resolveToneByScore = (value: number): EvaluationTone => {
  if (value >= 85) return "success";
  if (value >= 70) return "primary";
  if (value >= 55) return "warning";
  return "danger";
};

const resolveRiskTone = (unsafeRate: number): EvaluationTone => {
  if (unsafeRate <= 5) return "success";
  if (unsafeRate <= 12) return "warning";
  return "danger";
};

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
    value: formatMetricValue("performanceScore", report.scores.performanceScore),
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
      score: Number((normalizeRatio(report.rawStats.completionRate) * 100).toFixed(1)),
      value: formatRatioValue(report.rawStats.completionRate),
      description: "已完成样本占全部样本的比例。",
      tone: resolveToneByScore(report.rawStats.completionRate * 100),
    },
    {
      key: "successRate",
      label: "成功率",
      score: Number((normalizeRatio(report.rawStats.successRate) * 100).toFixed(1)),
      value: formatRatioValue(report.rawStats.successRate),
      description: "安全成功样本占全部样本的比例。",
      tone: resolveToneByScore(report.rawStats.successRate * 100),
    },
    {
      key: "conditionalSuccessRate",
      label: "条件成功率",
      score: Number(
        (normalizeRatio(report.rawStats.conditionalSuccessRate) * 100).toFixed(1),
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

export const getTrendMetricKeys = (
  trend: EvaluationScoreTrend | null,
  view: EvaluationScoreTrendView,
): EvaluationScoreMetricKey[] =>
  trend?.views[view]?.metrics ??
  (view === "risk"
    ? ["conservativeScore", "confidence", "unsafeRate"]
    : ["conservativeScore", "performanceScore", "hardScore"]);

export const selectRepresentativeSamples = (
  samples: EvaluationRepresentativeSamples,
): EvaluationRepresentativeSample[] => {
  const selected: EvaluationRepresentativeSample[] = [];
  if (samples.success) {
    selected.push(samples.success);
  }

  const riskSample = samples.failed ?? samples.error;
  if (riskSample) {
    selected.push(riskSample);
  }

  if (selected.length === 0 && samples.error) {
    selected.push(samples.error);
  }

  return selected.slice(0, 2);
};

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
    (item) => item.normalizedResult === "failed" || item.normalizedResult === "error",
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

const formatShortDate = (value: string | null): string => {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return `${String(date.getMonth() + 1).padStart(2, "0")}-${String(
    date.getDate(),
  ).padStart(2, "0")}`;
};

const shouldReduceMotion = (): boolean =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const baseChartOption = (): EChartsOption => ({
  backgroundColor: "transparent",
  animation: !shouldReduceMotion(),
  animationDuration: 520,
  animationEasing: "cubicOut",
  animationDurationUpdate: 280,
  animationEasingUpdate: "cubicOut",
  textStyle: {
    color: "#475569",
    fontFamily:
      'Inter, "Segoe UI", "Microsoft YaHei", system-ui, -apple-system, sans-serif',
  },
});

export const buildTrendLineOption = (
  trend: EvaluationScoreTrend | null,
  view: EvaluationScoreTrendView,
): EChartsOption => {
  const metricKeys = getTrendMetricKeys(trend, view);
  const items = trend?.items ?? [];

  return {
    ...baseChartOption(),
    color: metricKeys.map((key) => METRIC_COLORS[key]),
    grid: { left: 40, right: 20, top: 36, bottom: 44 },
    tooltip: {
      trigger: "axis",
      className: "evaluation-chart-tooltip",
      formatter: (params: unknown) => {
        const points = Array.isArray(params) ? params : [params];
        const firstPoint = points[0] as { dataIndex?: number } | undefined;
        const item =
          typeof firstPoint?.dataIndex === "number"
            ? items[firstPoint.dataIndex]
            : null;
        const lines = points
          .map((point) => {
            const typedPoint = point as {
              marker?: string;
              seriesName?: string;
              value?: number | null;
            };
            const value =
              typeof typedPoint.value === "number"
                ? formatNumber(typedPoint.value)
                : "未返回";
            return `${typedPoint.marker ?? ""}${typedPoint.seriesName ?? ""}：${value}`;
          })
          .join("<br/>");

        if (!item) {
          return lines;
        }

        return [
          `<strong>${item.agentName}</strong>`,
          `评测：${item.evaluationId}`,
          `完成：${formatShortDate(item.finishedAt ?? item.createdAt)}`,
          lines,
        ].join("<br/>");
      },
    },
    legend: {
      top: 0,
      right: 0,
      data: metricKeys.map((key) => getMetricLabel(key)),
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: "#475569" },
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: items.map((item) =>
        formatShortDate(item.finishedAt ?? item.createdAt),
      ),
      axisLine: { lineStyle: { color: "#cbd5e1" } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLabel: { color: "#64748b" },
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.18)" } },
    },
    series: metricKeys.map((key) => ({
      name: getMetricLabel(key),
      type: "line",
      smooth: true,
      symbol: "circle",
      symbolSize: 8,
      emphasis: {
        focus: "series",
        scale: 1.35,
      },
      lineStyle: { width: 3 },
      itemStyle: {
        borderColor: "#ffffff",
        borderWidth: 2,
      },
      areaStyle: { opacity: 0.1 },
      data: items.map((item) => item.scores[key] ?? null),
    })),
  };
};

export const buildRadarOption = (
  report: EvaluationReportPayload,
): EChartsOption => {
  const rows = buildRadarMetricRows(report);

  return {
    ...baseChartOption(),
    color: ["#2563eb"],
    radar: {
      radius: "66%",
      indicator: rows.map((row) => ({ name: row.label, max: 100 })),
      axisName: { color: "#475569" },
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.22)" } },
      splitArea: {
        areaStyle: { color: ["rgba(37, 99, 235, 0.04)", "transparent"] },
      },
      axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.28)" } },
    },
    tooltip: {},
    series: [
      {
        type: "radar",
        data: [{ value: rows.map((row) => row.score), name: "能力结构" }],
        areaStyle: { opacity: 0.2 },
        lineStyle: { width: 3 },
        symbolSize: 7,
      },
    ],
  };
};

export const buildRateOverviewOption = (
  report: EvaluationReportPayload,
): EChartsOption => {
  const rows = buildRateOverviewRows(report);

  return {
    ...baseChartOption(),
    color: ["#2563eb"],
    grid: { left: 78, right: 46, top: 22, bottom: 26 },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params: unknown) => {
        const points = Array.isArray(params) ? params : [params];
        const point = points.find((item) => {
          const typedPoint = item as { seriesName?: string };
          return typedPoint.seriesName === "结果率";
        }) as { dataIndex?: number } | undefined;
        const row =
          typeof point?.dataIndex === "number" ? rows[point.dataIndex] : null;

        return row
          ? `${row.label}：${row.value}<br/>${row.description}`
          : "";
      },
    },
    xAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLabel: { formatter: "{value}%" },
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.16)" } },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: rows.map((row) => row.label),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: "#475569", fontWeight: 700 },
    },
    series: [
      {
        name: "基线",
        type: "bar",
        silent: true,
        barWidth: 12,
        barGap: "-100%",
        data: rows.map(() => 100),
        itemStyle: {
          color: "rgba(148, 163, 184, 0.14)",
          borderRadius: 999,
        },
      },
      {
        name: "结果率",
        type: "bar",
        barWidth: 12,
        data: rows.map((row) => row.score),
        label: {
          show: true,
          position: "right",
          formatter: ({ dataIndex }: { dataIndex: number }) =>
            rows[dataIndex]?.value ?? "",
          color: "#334155",
          fontWeight: 800,
        },
        itemStyle: {
          color: "#2563eb",
          borderRadius: 999,
        },
      },
    ],
  };
};

export const buildConfidenceIntervalOption = (
  report: EvaluationReportPayload,
): EChartsOption => {
  const interval = buildConfidenceSummary(report);
  const width = Math.max(0, interval.high - interval.low);

  return {
    ...baseChartOption(),
    color: ["#2563eb", "#7c3aed"],
    grid: { left: 16, right: 24, top: 26, bottom: 28 },
    tooltip: {
      trigger: "axis",
      formatter: () =>
        `${interval.label}：${interval.value}<br/>${interval.caption}`,
    },
    xAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLabel: { color: "#64748b" },
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.14)" } },
    },
    yAxis: {
      type: "category",
      data: ["分数范围"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
    },
    series: [
      {
        name: "区间起点",
        type: "bar",
        stack: "confidence",
        silent: true,
        barWidth: 14,
        data: [interval.low],
        itemStyle: { color: "transparent" },
        emphasis: { disabled: true },
      },
      {
        name: "置信区间",
        type: "bar",
        stack: "confidence",
        barWidth: 14,
        data: [width],
        itemStyle: {
          color: "#2563eb",
          borderRadius: 999,
        },
      },
      {
        name: "中位数",
        type: "scatter",
        symbol: "diamond",
        symbolSize: 14,
        data: [[interval.median, "分数范围"]],
        itemStyle: {
          color: "#7c3aed",
          borderColor: "#ffffff",
          borderWidth: 2,
        },
      },
    ],
  };
};

export const buildOutcomeDonutOption = (
  report: EvaluationReportPayload,
): EChartsOption => ({
  ...baseChartOption(),
  color: [OUTCOME_COLORS.success, OUTCOME_COLORS.failed, OUTCOME_COLORS.error],
  tooltip: { trigger: "item" },
  legend: {
    bottom: 0,
    textStyle: { color: "#475569" },
  },
  series: [
    {
      name: "样本结果",
      type: "pie",
      radius: ["48%", "72%"],
      center: ["50%", "45%"],
      avoidLabelOverlap: true,
      itemStyle: {
        borderColor: "#ffffff",
        borderWidth: 3,
      },
      emphasis: {
        scale: true,
        scaleSize: 7,
      },
      label: { formatter: "{b}\n{c}" },
      data: [
        { name: "成功", value: report.breakdowns.outcomeSummary.success },
        { name: "失败", value: report.breakdowns.outcomeSummary.failed },
        { name: "异常", value: report.breakdowns.outcomeSummary.error },
      ],
    },
  ],
});

export const buildDifficultyBarOption = (
  report: EvaluationReportPayload,
): EChartsOption => ({
  ...baseChartOption(),
  color: [
    OUTCOME_COLORS.success,
    OUTCOME_COLORS.failed,
    OUTCOME_COLORS.error,
    "#2563eb",
  ],
  tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
  legend: { top: 0, right: 0, textStyle: { color: "#475569" } },
  grid: { left: 40, right: 48, top: 44, bottom: 38 },
  xAxis: {
    type: "category",
    data: report.breakdowns.difficultyBuckets.map((item) => item.bucket),
    axisTick: { show: false },
    axisLine: { lineStyle: { color: "#cbd5e1" } },
  },
  yAxis: [
    {
      type: "value",
      name: "样本",
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.18)" } },
    },
    {
      type: "value",
      name: "成功率",
      min: 0,
      max: 100,
      axisLabel: { formatter: "{value}%" },
      splitLine: { show: false },
    },
  ],
  series: [
    ...(["success", "failed", "error"] as EvaluationSampleOutcome[]).map(
      (key) => ({
        name: key === "success" ? "成功" : key === "failed" ? "失败" : "异常",
        type: "bar" as const,
        stack: "difficulty",
        barMaxWidth: 34,
        emphasis: { focus: "series" as const },
        data: report.breakdowns.difficultyBuckets.map((item) => item[key]),
      }),
    ),
    {
      name: "成功率",
      type: "line",
      yAxisIndex: 1,
      smooth: true,
      symbol: "circle",
      symbolSize: 8,
      lineStyle: { width: 3 },
      itemStyle: { borderColor: "#ffffff", borderWidth: 2 },
      data: report.breakdowns.difficultyBuckets.map((item) =>
        Number((normalizeRatio(item.successRate) * 100).toFixed(1)),
      ),
    },
  ],
});

export const buildDatasetStackedBarOption = (
  report: EvaluationReportPayload,
): EChartsOption => ({
  ...baseChartOption(),
  color: [OUTCOME_COLORS.success, OUTCOME_COLORS.failed, OUTCOME_COLORS.error],
  tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
  legend: { top: 0, right: 0, textStyle: { color: "#475569" } },
  grid: { left: 126, right: 24, top: 44, bottom: 32 },
  xAxis: {
    type: "value",
    splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.18)" } },
  },
  yAxis: {
    type: "category",
    inverse: true,
    data: report.breakdowns.datasetSummaries.map((item) => item.datasetName),
    axisLabel: {
      color: "#475569",
      fontWeight: 700,
      overflow: "truncate",
      width: 112,
    },
    axisTick: { show: false },
    axisLine: { lineStyle: { color: "#cbd5e1" } },
  },
  series: ["success", "failed", "error"].map((key) => ({
    name: key === "success" ? "成功" : key === "failed" ? "失败" : "异常",
    type: "bar",
    stack: "dataset",
    barMaxWidth: 26,
    emphasis: { focus: "series" },
    data: report.breakdowns.datasetSummaries.map(
      (item) => item[key as EvaluationSampleOutcome],
    ),
  })),
});

export const buildSampleScatterOption = (
  report: EvaluationReportPayload,
): EChartsOption => ({
  ...baseChartOption(),
  color: [OUTCOME_COLORS.success, OUTCOME_COLORS.failed, OUTCOME_COLORS.error],
  tooltip: {
    trigger: "item",
    formatter: (params: any) => {
      const value = params.value ?? [];
      return `难度：${value[0]}<br/>耗时：${value[1]} ms<br/>样本：${value[2]}`;
    },
  },
  legend: { top: 0, right: 0, textStyle: { color: "#475569" } },
  grid: { left: 54, right: 18, top: 42, bottom: 42 },
  xAxis: {
    type: "value",
    min: 0,
    max: 1,
    name: "难度",
    splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.16)" } },
  },
  yAxis: {
    type: "value",
    name: "耗时 ms",
    splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.16)" } },
  },
  series: (["success", "failed", "error"] as EvaluationSampleOutcome[]).map(
    (outcome) => ({
      name:
        outcome === "success" ? "成功" : outcome === "failed" ? "失败" : "异常",
      type: "scatter",
      symbolSize: outcome === "success" ? 8 : 10,
      emphasis: {
        focus: "series",
        scale: 1.35,
      },
      data: report.breakdowns.sampleScatterPoints
        .filter((item) => item.normalizedResult === outcome)
        .map((item) => [item.difficulty, item.durationMs, item.sampleId]),
    }),
  ),
});
