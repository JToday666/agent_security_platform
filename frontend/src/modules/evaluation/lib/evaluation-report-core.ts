import type { EChartsOption } from "echarts";
import {
  type AppTranslator,
  translateRuntimeMessage,
} from "@/app/i18n/runtime-translator";
import type {
  EvaluationSampleOutcome,
  EvaluationScoreMetricKey,
} from "@/shared/types/agent-types";

export interface MetricDefinition {
  key: EvaluationScoreMetricKey;
  label: string;
  description: string;
  unit?: "%";
}

export type EvaluationTone =
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "neutral";

const METRIC_DEFINITION_BASE: Array<Pick<MetricDefinition, "key" | "unit">> = [
  {
    key: "conservativeScore",
  },
  {
    key: "performanceScore",
  },
  {
    key: "confidence",
  },
  {
    key: "completionScore",
  },
  {
    key: "safetyScore",
  },
  {
    key: "hardScore",
  },
  {
    key: "unsafeRate",
    unit: "%",
  },
  {
    key: "timeScore",
  },
];

export const getMetricDefinitions = (
  t: AppTranslator = translateRuntimeMessage,
): MetricDefinition[] =>
  METRIC_DEFINITION_BASE.map((definition) => ({
    ...definition,
    label: t(`evaluation.metrics.${definition.key}.label`),
    description: t(`evaluation.metrics.${definition.key}.description`),
  }));

export const METRIC_COLORS: Record<EvaluationScoreMetricKey, string> = {
  conservativeScore: "#2563eb",
  performanceScore: "#0f766e",
  confidence: "#7c3aed",
  completionScore: "#0891b2",
  safetyScore: "#16a34a",
  hardScore: "#ea580c",
  unsafeRate: "#dc2626",
  timeScore: "#4f46e5",
};

export const OUTCOME_COLORS: Record<EvaluationSampleOutcome, string> = {
  success: "#16a34a",
  failed: "#dc2626",
  error: "#f59e0b",
};

export const METRIC_TONES: Record<EvaluationScoreMetricKey, EvaluationTone> = {
  conservativeScore: "primary",
  performanceScore: "success",
  confidence: "primary",
  completionScore: "success",
  safetyScore: "success",
  hardScore: "warning",
  unsafeRate: "danger",
  timeScore: "primary",
};

export const getMetricLabel = (
  key: EvaluationScoreMetricKey,
  t: AppTranslator = translateRuntimeMessage,
): string => t(`evaluation.metrics.${key}.label`);

export const formatNumber = (value: number): string =>
  Number.isFinite(value) ? value.toFixed(1) : "0.0";

export const clampScore = (value: number): number =>
  Number(
    Math.min(100, Math.max(0, Number.isFinite(value) ? value : 0)).toFixed(1),
  );

export const normalizeRatio = (value: number): number =>
  Number(
    Math.min(1, Math.max(0, Number.isFinite(value) ? value : 0)).toFixed(4),
  );

export const formatMetricValue = (
  key: EvaluationScoreMetricKey,
  value: number,
): string => {
  const definition = METRIC_DEFINITION_BASE.find((item) => item.key === key);
  return definition?.unit === "%"
    ? `${formatNumber(value)}%`
    : formatNumber(value);
};

export const formatPercentValue = (value: number): string =>
  `${formatNumber(value * 100)}%`;

export const formatRatioValue = (value: number): string =>
  formatPercentValue(normalizeRatio(value));

export const resolveToneByScore = (value: number): EvaluationTone => {
  if (value >= 85) return "success";
  if (value >= 70) return "primary";
  if (value >= 55) return "warning";
  return "danger";
};

export const resolveRiskTone = (unsafeRate: number): EvaluationTone => {
  if (unsafeRate <= 5) return "success";
  if (unsafeRate <= 12) return "warning";
  return "danger";
};

export const formatShortDate = (value: string | null): string => {
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
  typeof window.matchMedia === "function" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export const baseChartOption = (): EChartsOption => ({
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
