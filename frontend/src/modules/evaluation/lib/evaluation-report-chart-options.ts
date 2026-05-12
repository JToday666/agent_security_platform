import type { EChartsOption } from "echarts";
import {
  type AppTranslator,
  translateRuntimeMessage,
} from "@/app/i18n/runtime-translator";
import {
  baseChartOption,
  formatNumber,
  formatShortDate,
  getMetricLabel,
  METRIC_COLORS,
  normalizeRatio,
  OUTCOME_COLORS,
} from "@/modules/evaluation/lib/evaluation-report-core";
import {
  buildConfidenceSummary,
  buildRadarMetricRows,
  buildRateOverviewRows,
} from "@/modules/evaluation/lib/evaluation-report-metrics";
import type {
  EvaluationReportPayload,
  EvaluationSampleOutcome,
  EvaluationScoreMetricKey,
  EvaluationScoreTrend,
  EvaluationScoreTrendView,
} from "@/shared/types/agent-types";

export const getTrendMetricKeys = (
  trend: EvaluationScoreTrend | null,
  view: EvaluationScoreTrendView,
): EvaluationScoreMetricKey[] =>
  trend?.views[view]?.metrics ??
  (view === "risk"
    ? ["conservativeScore", "confidence", "unsafeRate"]
    : ["conservativeScore", "performanceScore", "hardScore"]);

export const buildTrendLineOption = (
  trend: EvaluationScoreTrend | null,
  view: EvaluationScoreTrendView,
  t: AppTranslator = translateRuntimeMessage,
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
                : t("evaluation.common.noReturn");
            return `${typedPoint.marker ?? ""}${typedPoint.seriesName ?? ""}：${value}`;
          })
          .join("<br/>");

        if (!item) {
          return lines;
        }

        return [
          `<strong>${item.agentName}</strong>`,
          t("evaluation.charts.evaluationId", { id: item.evaluationId }),
          t("evaluation.charts.completionDate", {
            date: formatShortDate(item.finishedAt ?? item.createdAt),
          }),
          lines,
        ].join("<br/>");
      },
    },
    legend: {
      top: 0,
      right: 0,
      data: metricKeys.map((key) => getMetricLabel(key, t)),
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
      name: getMetricLabel(key, t),
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
  t: AppTranslator = translateRuntimeMessage,
): EChartsOption => {
  const rows = buildRadarMetricRows(report, t);

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
        data: [
          {
            value: rows.map((row) => row.score),
            name: t("evaluation.charts.abilityStructure"),
          },
        ],
        areaStyle: { opacity: 0.2 },
        lineStyle: { width: 3 },
        symbolSize: 7,
      },
    ],
  };
};

export const buildRateOverviewOption = (
  report: EvaluationReportPayload,
  t: AppTranslator = translateRuntimeMessage,
): EChartsOption => {
  const rows = buildRateOverviewRows(report, t);
  const outcomeRateName = t("evaluation.charts.outcomeRate");

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
          return typedPoint.seriesName === outcomeRateName;
        }) as { dataIndex?: number } | undefined;
        const row =
          typeof point?.dataIndex === "number" ? rows[point.dataIndex] : null;

        return row ? `${row.label}：${row.value}<br/>${row.description}` : "";
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
        name: t("evaluation.charts.baseline"),
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
        name: outcomeRateName,
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
  t: AppTranslator = translateRuntimeMessage,
): EChartsOption => {
  const interval = buildConfidenceSummary(report, t);
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
      data: [t("evaluation.charts.scoreRange")],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
    },
    series: [
      {
        name: t("evaluation.charts.seriesStart"),
        type: "bar",
        stack: "confidence",
        silent: true,
        barWidth: 14,
        data: [interval.low],
        itemStyle: { color: "transparent" },
        emphasis: { disabled: true },
      },
      {
        name: interval.label,
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
        name: t("evaluation.charts.median"),
        type: "scatter",
        symbol: "diamond",
        symbolSize: 14,
        data: [[interval.median, t("evaluation.charts.scoreRange")]],
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
  t: AppTranslator = translateRuntimeMessage,
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
      name: t("evaluation.report.outcomeSection"),
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
        {
          name: t("evaluation.outcomes.success"),
          value: report.breakdowns.outcomeSummary.success,
        },
        {
          name: t("evaluation.outcomes.failed"),
          value: report.breakdowns.outcomeSummary.failed,
        },
        {
          name: t("evaluation.outcomes.error"),
          value: report.breakdowns.outcomeSummary.error,
        },
      ],
    },
  ],
});

export const buildDifficultyBarOption = (
  report: EvaluationReportPayload,
  t: AppTranslator = translateRuntimeMessage,
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
      name: t("evaluation.charts.sample"),
      splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.18)" } },
    },
    {
      type: "value",
      name: t("evaluation.charts.successRate"),
      min: 0,
      max: 100,
      axisLabel: { formatter: "{value}%" },
      splitLine: { show: false },
    },
  ],
  series: [
    ...(["success", "failed", "error"] as EvaluationSampleOutcome[]).map(
      (key) => ({
        name: t(`evaluation.outcomes.${key}`),
        type: "bar" as const,
        stack: "difficulty",
        barMaxWidth: 34,
        emphasis: { focus: "series" as const },
        data: report.breakdowns.difficultyBuckets.map((item) => item[key]),
      }),
    ),
    {
      name: t("evaluation.charts.successRate"),
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
  t: AppTranslator = translateRuntimeMessage,
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
    name: t(`evaluation.outcomes.${key}`),
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
  t: AppTranslator = translateRuntimeMessage,
): EChartsOption => ({
  ...baseChartOption(),
  color: [OUTCOME_COLORS.success, OUTCOME_COLORS.failed, OUTCOME_COLORS.error],
  tooltip: {
    trigger: "item",
    formatter: (params: any) => {
      const value = params.value ?? [];
      return t("evaluation.charts.sampleTooltip", {
        difficulty: value[0],
        duration: value[1],
        sampleId: value[2],
      });
    },
  },
  legend: { top: 0, right: 0, textStyle: { color: "#475569" } },
  grid: { left: 54, right: 18, top: 42, bottom: 42 },
  xAxis: {
    type: "value",
    min: 0,
    max: 1,
    name: t("evaluation.charts.difficulty"),
    splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.16)" } },
  },
  yAxis: {
    type: "value",
    name: t("evaluation.charts.durationMs"),
    splitLine: { lineStyle: { color: "rgba(148, 163, 184, 0.16)" } },
  },
  series: (["success", "failed", "error"] as EvaluationSampleOutcome[]).map(
    (outcome) => ({
      name:
        t(`evaluation.outcomes.${outcome}`),
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
