import type { RangeMeta } from "@/types/AgentTypes";

const countDecimals = (value: number): number => {
  const text = value.toString();
  const index = text.indexOf(".");
  return index === -1 ? 0 : text.length - index - 1;
};

const clamp = (value: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, value));

const normalizeToStep = (value: number, meta: RangeMeta): number => {
  const precision = Math.max(countDecimals(meta.step), countDecimals(meta.min));
  const stepped =
    Math.round((value - meta.min) / meta.step) * meta.step + meta.min;

  return Number(stepped.toFixed(Math.max(precision, 0)));
};

const toFiniteNumber = (value: unknown, fallback: number): number => {
  const normalized =
    typeof value === "number" ? value : Number.parseFloat(String(value));

  return Number.isFinite(normalized) ? normalized : fallback;
};

export const normalizeDifficulty = (
  value: unknown,
  meta: RangeMeta,
): number => {
  const clamped = clamp(
    toFiniteNumber(value, meta.default),
    meta.min,
    meta.max,
  );
  return Number(normalizeToStep(clamped, meta).toFixed(1));
};

export const normalizeTimeoutMinutes = (
  value: unknown,
  meta: RangeMeta,
): number => {
  const clamped = clamp(
    toFiniteNumber(value, meta.default),
    meta.min,
    meta.max,
  );
  return Math.round(normalizeToStep(clamped, meta));
};

export const isStepAligned = (value: number, meta: RangeMeta): boolean => {
  const stepped = (value - meta.min) / meta.step;
  return Number.isInteger(Number(stepped.toFixed(6)));
};

export const getRangeSoftWarning = (
  value: number,
  meta: RangeMeta,
  fallbackThreshold = meta.max,
): string => {
  const threshold = meta.recommendedMax ?? fallbackThreshold;

  if (value <= threshold) {
    return "";
  }

  return `当前设置高于建议值 ${threshold}，可能增加等待和执行耗时。`;
};
