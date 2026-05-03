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

const formatMetricValue = (
  key: EvaluationScoreMetricKey,
  value: number,
): string => {
  const definition = METRIC_DEFINITIONS.find((item) => item.key === key);
  return definition?.unit === "%" ? `${formatNumber(value)}%` : formatNumber(value);
};

const formatPercentValue = (value: number): string =>
  `${formatNumber(value * 100)}%`;

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
  const metricKey =
    view === "risk" ? "unsafeRate" : "conservativeScore";
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
    value: formatMetricValue("conservativeScore", report.scores.conservativeScore),
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

export const buildReportInsights = (
  report: EvaluationReportPayload,
): EvaluationReportInsight[] => {
  const outcome = report.breakdowns.outcomeSummary;
  const total = Math.max(1, outcome.success + outcome.failed + outcome.error);
  const successRate = outcome.success / total;
  const hardestBucket = report.breakdowns.difficultyBuckets.length
    ? report.breakdowns.difficultyBuckets.reduce((current, item) =>
        item.successRate < current.successRate ? item : current,
      )
    : null;
  const weakestDataset = report.breakdowns.datasetSummaries.length
    ? report.breakdowns.datasetSummaries.reduce((current, item) => {
        const currentRisk = current.failed + current.error;
        const nextRisk = item.failed + item.error;
        return nextRisk > currentRisk ? item : current;
      })
    : null;
  const slowestPoint = report.breakdowns.sampleScatterPoints.length
    ? report.breakdowns.sampleScatterPoints.reduce((current, item) =>
        item.durationMs > current.durationMs ? item : current,
      )
    : null;

  return [
    {
      title: "能力结构",
      value: formatMetricValue("performanceScore", report.scores.performanceScore),
      caption: "综合完成、安全、高难和速度后的表现分。",
      tone: resolveToneByScore(report.scores.performanceScore),
    },
    {
      title: "样本结果",
      value: formatPercentValue(successRate),
      caption: `成功 ${outcome.success} 个，失败 ${outcome.failed} 个，异常 ${outcome.error} 个。`,
      tone: resolveToneByScore(successRate * 100),
    },
    {
      title: "难度桶",
      value: hardestBucket?.bucket ?? "未返回",
      caption: hardestBucket
        ? `该区间成功率 ${formatPercentValue(hardestBucket.successRate)}。`
        : "暂无难度桶数据。",
      tone: hardestBucket && hardestBucket.successRate < 0.6 ? "warning" : "primary",
    },
    {
      title: "数据集结果",
      value: weakestDataset?.datasetName ?? "未返回",
      caption: weakestDataset
        ? `失败 ${weakestDataset.failed} 个，异常 ${weakestDataset.error} 个。`
        : "暂无数据集结果。",
      tone:
        weakestDataset && weakestDataset.failed + weakestDataset.error > 0
          ? "warning"
          : "success",
    },
    {
      title: "样本耗时",
      value: slowestPoint ? `${Math.round(slowestPoint.durationMs / 1000)}s` : "未返回",
      caption: slowestPoint
        ? `最慢样本 ${slowestPoint.sampleId}。`
        : "暂无散点样本。",
      tone: "neutral",
    },
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
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: "#475569" },
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: items.map((item) => formatShortDate(item.finishedAt ?? item.createdAt)),
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

export const buildRadarOption = (report: EvaluationReportPayload): EChartsOption => {
  const values = [
    report.scores.performanceScore,
    report.scores.completionScore,
    report.scores.safetyScore,
    report.scores.hardScore,
    report.scores.timeScore,
    Math.max(0, 100 - report.scores.unsafeRate),
  ];

  return {
    ...baseChartOption(),
    color: ["#2563eb"],
    radar: {
      radius: "66%",
      indicator: [
        { name: "表现分", max: 100 },
        { name: "完成能力", max: 100 },
        { name: "安全识别", max: 100 },
        { name: "高难表现", max: 100 },
        { name: "速度", max: 100 },
        { name: "安全稳定", max: 100 },
      ],
      axisName: { color: "#475569" },
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.22)" } },
      splitArea: { areaStyle: { color: ["rgba(37, 99, 235, 0.04)", "transparent"] } },
      axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.28)" } },
    },
    tooltip: {},
    series: [
      {
        type: "radar",
        data: [{ value: values, name: "能力结构" }],
        areaStyle: { opacity: 0.2 },
        lineStyle: { width: 3 },
        symbolSize: 7,
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
  color: [OUTCOME_COLORS.success, OUTCOME_COLORS.failed, OUTCOME_COLORS.error],
  tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
  legend: { top: 0, right: 0, textStyle: { color: "#475569" } },
  grid: { left: 40, right: 18, top: 42, bottom: 38 },
  xAxis: {
    type: "category",
    data: report.breakdowns.difficultyBuckets.map((item) => item.bucket),
    axisTick: { show: false },
    axisLine: { lineStyle: { color: "#cbd5e1" } },
  },
  yAxis: {
    type: "value",
    splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.18)" } },
  },
  series: ["success", "failed", "error"].map((key) => ({
    name: key === "success" ? "成功" : key === "failed" ? "失败" : "异常",
    type: "bar",
    stack: "difficulty",
    barMaxWidth: 34,
    emphasis: { focus: "series" },
    data: report.breakdowns.difficultyBuckets.map(
      (item) => item[key as EvaluationSampleOutcome],
    ),
  })),
});

export const buildDatasetStackedBarOption = (
  report: EvaluationReportPayload,
): EChartsOption => ({
  ...baseChartOption(),
  color: [OUTCOME_COLORS.success, OUTCOME_COLORS.failed, OUTCOME_COLORS.error],
  tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
  legend: { top: 0, right: 0, textStyle: { color: "#475569" } },
  grid: { left: 42, right: 18, top: 42, bottom: 68 },
  xAxis: {
    type: "category",
    data: report.breakdowns.datasetSummaries.map((item) => item.datasetName),
    axisLabel: { interval: 0, rotate: 28 },
    axisTick: { show: false },
    axisLine: { lineStyle: { color: "#cbd5e1" } },
  },
  yAxis: {
    type: "value",
    splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.18)" } },
  },
  series: ["success", "failed", "error"].map((key) => ({
    name: key === "success" ? "成功" : key === "failed" ? "失败" : "异常",
    type: "bar",
    stack: "dataset",
    barMaxWidth: 36,
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
      name: outcome === "success" ? "成功" : outcome === "failed" ? "失败" : "异常",
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
