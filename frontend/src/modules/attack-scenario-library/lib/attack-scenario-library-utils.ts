import { formatDateTime, formatNumber } from "@/app/i18n/intl-format";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";

export interface ScenarioTheme {
  soft: string;
  solid: string;
  border: string;
  text: string;
  gradient: string;
  shadow: string;
}

interface ScenarioPalette {
  hue: number;
  saturation: number;
  lightness: number;
}

const DEFAULT_THEME_ID = "__default__";
const ACCENT_HUE_OFFSET = 7;

const KNOWN_ATTACK_SCENARIO_PALETTE: Record<string, ScenarioPalette> = {
  prompt_injection: { hue: 220, saturation: 62, lightness: 45 },
  model_abuse_and_unauthorized_actions: {
    hue: 340,
    saturation: 58,
    lightness: 43,
  },
  knowledge_base_poisoning: { hue: 154, saturation: 50, lightness: 34 },
  tool_call_hijacking: { hue: 38, saturation: 70, lightness: 41 },
};

const GENERATED_SCENARIO_PALETTE: ScenarioPalette[] = [
  { hue: 108, saturation: 52, lightness: 36 },
  { hue: 12, saturation: 64, lightness: 43 },
  { hue: 132, saturation: 50, lightness: 35 },
  { hue: 312, saturation: 46, lightness: 44 },
  { hue: 60, saturation: 64, lightness: 39 },
  { hue: 269, saturation: 50, lightness: 48 },
  { hue: 84, saturation: 54, lightness: 35 },
  { hue: 194, saturation: 64, lightness: 38 },
];

const clamp = (value: number, minimum: number, maximum: number): number =>
  Math.min(maximum, Math.max(minimum, value));

const normalizeHue = (value: number): number => {
  const normalized = value % 360;

  return normalized < 0 ? normalized + 360 : normalized;
};

const hashThemeId = (value: string): number => {
  let hash = 2166136261;

  for (const char of value) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }

  return hash >>> 0;
};

const toHsl = (hue: number, saturation: number, lightness: number): string =>
  `hsl(${Math.round(normalizeHue(hue))} ${saturation}% ${lightness}%)`;

const toHsla = (
  hue: number,
  saturation: number,
  lightness: number,
  alpha: number,
): string =>
  `hsla(${Math.round(normalizeHue(hue))}, ${saturation}%, ${lightness}%, ${alpha})`;

const normalizeThemeId = (themeId: string): string =>
  themeId.trim() || DEFAULT_THEME_ID;

const buildThemeFromPalette = (
  hue: number,
  saturation: number,
  lightness: number,
): ScenarioTheme => {
  const accentHue = normalizeHue(hue + ACCENT_HUE_OFFSET);

  return {
    soft: toHsl(hue, 64, 97),
    solid: toHsl(hue, saturation, lightness),
    border: toHsl(hue, 52, 86),
    text: toHsl(hue, 38, 30),
    gradient: `linear-gradient(135deg, ${toHsl(hue, saturation, Math.max(32, lightness - 3))}, ${toHsl(accentHue, Math.max(42, saturation - 6), Math.min(56, lightness + 5))})`,
    shadow: toHsla(hue, 36, 40, 0.16),
  };
};

const buildScenarioTheme = (palette: ScenarioPalette): ScenarioTheme =>
  buildThemeFromPalette(palette.hue, palette.saturation, palette.lightness);

export const getAttackScenarioTheme = (
  attackScenarioId: string,
): ScenarioTheme => {
  const themeId = normalizeThemeId(attackScenarioId);
  const knownPalette = KNOWN_ATTACK_SCENARIO_PALETTE[themeId];

  if (knownPalette) {
    return buildScenarioTheme(knownPalette);
  }

  const seed = hashThemeId(themeId);
  const generated =
    GENERATED_SCENARIO_PALETTE[seed % GENERATED_SCENARIO_PALETTE.length];
  return buildScenarioTheme({
    hue: normalizeHue(generated.hue + (seed % 13) - 6),
    saturation: clamp(generated.saturation + ((seed >>> 3) % 7) - 3, 42, 68),
    lightness: clamp(generated.lightness + ((seed >>> 6) % 7) - 3, 34, 50),
  });
};

export const getRiskDomainTheme = (
  attackScenarioId: string,
  riskDomainId: string,
  riskDomainIds: readonly string[],
): ScenarioTheme => {
  const scenarioTheme = getAttackScenarioTheme(attackScenarioId);
  const baseHue = Number(
    scenarioTheme.solid.match(/hsl\((\d+)/)?.[1] ?? "220",
  );
  const index = Math.max(0, riskDomainIds.indexOf(riskDomainId));
  const seed = hashThemeId(`${attackScenarioId}:${riskDomainId}`);
  const hueOffset = ((index % 5) - 2) * 7 + (seed % 5);

  return buildThemeFromPalette(
    normalizeHue(baseHue + hueOffset),
    54,
    40 + (index % 3),
  );
};

export const formatDateLabel = (value?: string): string => {
  if (!value) {
    return translateRuntimeMessage("attackScenarioLibrary.fallback.pending");
  }

  return formatDateTime(value, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
};

export const formatDateTimeLabel = (value?: string): string => {
  if (!value) {
    return translateRuntimeMessage("attackScenarioLibrary.fallback.pending");
  }

  return formatDateTime(value, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const formatSampleCount = (value?: number): string => {
  if (typeof value !== "number") {
    return translateRuntimeMessage("attackScenarioLibrary.fallback.pending");
  }

  return formatNumber(value);
};
