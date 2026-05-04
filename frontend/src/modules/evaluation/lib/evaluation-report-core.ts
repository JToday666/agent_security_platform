import type { EChartsOption } from "echarts";
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

export const METRIC_DEFINITIONS: MetricDefinition[] = [
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

export const getMetricLabel = (key: EvaluationScoreMetricKey): string =>
  METRIC_DEFINITIONS.find((item) => item.key === key)?.label ?? key;

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
  const definition = METRIC_DEFINITIONS.find((item) => item.key === key);
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
