import type {
  DatasetCategory,
  DatasetSubcategory,
} from "@/shared/types/dataset-types";
import { formatDateTime, formatNumber } from "@/app/i18n/intl-format";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import { MAX_SUBMIT_DATASET_COUNT } from "@/modules/submission/model/parameter-validator";

export interface CategoryTheme {
  soft: string;
  solid: string;
  border: string;
  text: string;
  gradient: string;
  shadow: string;
}

interface CategoryPalette {
  hue: number;
  saturation: number;
  lightness: number;
}

const DEFAULT_CATEGORY_THEME_ID = "__default__";
const MAX_RISK_DOMAIN_THEME_SLOTS = 15;
const MIN_THEME_HUE_GAP = 16;
const ACCENT_HUE_OFFSET = 7;

const KNOWN_CATEGORY_PALETTE: Record<string, CategoryPalette> = {
  confidentiality: { hue: 220, saturation: 62, lightness: 45 },
  integrity: { hue: 170, saturation: 54, lightness: 34 },
  availability_and_destructive_harm: { hue: 36, saturation: 72, lightness: 42 },
  unauthorized_execution_and_system_control: {
    hue: 252,
    saturation: 58,
    lightness: 52,
  },
  fraud_impersonation_and_social_engineering: {
    hue: 338,
    saturation: 58,
    lightness: 43,
  },
  content_and_societal_harm: { hue: 194, saturation: 64, lightness: 38 },
  harmful_search_and_reconnaissance: {
    hue: 286,
    saturation: 48,
    lightness: 45,
  },
};

const GENERATED_CATEGORY_PALETTE: CategoryPalette[] = [
  { hue: 108, saturation: 52, lightness: 36 },
  { hue: 12, saturation: 64, lightness: 43 },
  { hue: 132, saturation: 50, lightness: 35 },
  { hue: 312, saturation: 46, lightness: 44 },
  { hue: 60, saturation: 64, lightness: 39 },
  { hue: 269, saturation: 50, lightness: 48 },
  { hue: 84, saturation: 54, lightness: 35 },
  { hue: 154, saturation: 48, lightness: 34 },
  { hue: 236, saturation: 50, lightness: 48 },
  { hue: 320, saturation: 48, lightness: 43 },
  { hue: 300, saturation: 48, lightness: 45 },
  { hue: 148, saturation: 46, lightness: 35 },
  { hue: 72, saturation: 58, lightness: 36 },
  { hue: 120, saturation: 48, lightness: 36 },
  { hue: 4, saturation: 62, lightness: 43 },
];

const hashCategoryId = (value: string): number => {
  let hash = 2166136261;

  for (const char of value) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }

  return hash >>> 0;
};

const mixHash = (value: number): number => {
  let hash = value >>> 0;

  hash ^= hash >>> 16;
  hash = Math.imul(hash, 2246822507) >>> 0;
  hash ^= hash >>> 13;
  hash = Math.imul(hash, 3266489909) >>> 0;
  hash ^= hash >>> 16;

  return hash >>> 0;
};

const clamp = (value: number, minimum: number, maximum: number): number =>
  Math.min(maximum, Math.max(minimum, value));

const normalizeHue = (value: number): number => {
  const normalized = value % 360;

  return normalized < 0 ? normalized + 360 : normalized;
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

const compareCategoryIds = (left: string, right: string): number =>
  left.localeCompare(right);

const normalizeCategoryThemeId = (categoryId: string): string =>
  categoryId.trim() || DEFAULT_CATEGORY_THEME_ID;

const normalizeCategoryThemeIds = (categoryIds: readonly string[]): string[] =>
  Array.from(new Set(categoryIds.map(normalizeCategoryThemeId))).sort(
    compareCategoryIds,
  );

const getHueDistance = (left: number, right: number): number => {
  const delta = Math.abs(normalizeHue(left - right));
  return delta > 180 ? 360 - delta : delta;
};

const getMinimumHueDistance = (hue: number, usedHues: readonly number[]): number => {
  if (usedHues.length === 0) {
    return 180;
  }

  return Math.min(...usedHues.map((item) => getHueDistance(hue, item)));
};

const resolvePaletteHue = (
  palette: CategoryPalette,
  seed: number,
  usedHues: readonly number[],
): number => {
  const baseHue = normalizeHue(palette.hue);

  if (getMinimumHueDistance(baseHue, usedHues) >= MIN_THEME_HUE_GAP) {
    return baseHue;
  }

  const direction = seed % 2 === 0 ? 1 : -1;
  const step = 5 + (seed % 5);
  let bestHue = baseHue;
  let bestDistance = getMinimumHueDistance(baseHue, usedHues);

  for (let attempt = 1; attempt <= 32; attempt += 1) {
    const candidates = [
      normalizeHue(baseHue + direction * step * attempt),
      normalizeHue(baseHue - direction * step * attempt),
    ];

    for (const candidateHue of candidates) {
      const distance = getMinimumHueDistance(candidateHue, usedHues);

      if (distance > bestDistance) {
        bestHue = candidateHue;
        bestDistance = distance;
      }

      if (distance >= MIN_THEME_HUE_GAP) {
        return candidateHue;
      }
    }
  }

  return bestHue;
};

const resolveGeneratedPalette = (
  categoryId: string,
  usedHues: readonly number[],
  usedCandidateIndexes: ReadonlySet<number>,
): CategoryPalette & { candidateIndex?: number } => {
  const seed = hashCategoryId(categoryId);
  const candidates = GENERATED_CATEGORY_PALETTE.slice(
    0,
    MAX_RISK_DOMAIN_THEME_SLOTS,
  )
    .map((palette, index) => {
      const resolvedHue = resolvePaletteHue(
        palette,
        mixHash(seed ^ index),
        usedHues,
      );

      return {
        ...palette,
        hue: resolvedHue,
        hueAdjusted: resolvedHue !== normalizeHue(palette.hue),
        index,
        distance: getMinimumHueDistance(resolvedHue, usedHues),
        score: mixHash(seed ^ hashCategoryId(`theme-slot:${index}`)),
      };
    })
    .sort(
      (left, right) =>
        Number(usedCandidateIndexes.has(left.index)) -
          Number(usedCandidateIndexes.has(right.index)) ||
        right.distance - left.distance ||
        left.score - right.score ||
        left.index - right.index,
    );

  const selectedCandidate =
    candidates.find(
      (candidate) =>
        !usedCandidateIndexes.has(candidate.index) &&
        candidate.distance >= MIN_THEME_HUE_GAP,
    ) ??
    candidates.find((candidate) => !usedCandidateIndexes.has(candidate.index)) ??
    candidates[0];

  if (selectedCandidate) {
    const { hue, hueAdjusted, index, saturation, lightness } = selectedCandidate;

    return {
      hue,
      saturation: clamp(
        saturation + (((seed >>> 3) % 3) - 1) * 2 - (hueAdjusted ? 2 : 0),
        42,
        66,
      ),
      lightness: clamp(
        lightness + (((seed >>> 5) % 3) - 1) + (hueAdjusted ? 1 : 0),
        34,
        50,
      ),
      candidateIndex: index,
    };
  }

  return {
    hue: resolvePaletteHue(
      { hue: seed % 360, saturation: 52, lightness: 42 },
      seed,
      usedHues,
    ),
    saturation: 52,
    lightness: 42,
  };
};

const buildCategoryThemeFromPalette = (
  baseHue: number,
  saturation: number,
  lightness: number,
): CategoryTheme => {
  const accentHue = normalizeHue(baseHue + ACCENT_HUE_OFFSET);

  return {
    soft: toHsl(baseHue, 64, 97),
    solid: toHsl(baseHue, saturation, lightness),
    border: toHsl(baseHue, 52, 86),
    text: toHsl(baseHue, 38, 30),
    gradient: `linear-gradient(135deg, ${toHsl(baseHue, saturation, Math.max(32, lightness - 3))}, ${toHsl(accentHue, Math.max(42, saturation - 6), Math.min(56, lightness + 5))})`,
    shadow: toHsla(baseHue, 36, 40, 0.16),
  };
};

const buildCategoryTheme = (palette: CategoryPalette): CategoryTheme =>
  buildCategoryThemeFromPalette(
    palette.hue,
    palette.saturation,
    palette.lightness,
  );

export const getCategoryThemeMap = (
  categoryIds: readonly string[],
): Map<string, CategoryTheme> => {
  const ids = normalizeCategoryThemeIds(categoryIds);
  const usedHues = Object.values(KNOWN_CATEGORY_PALETTE).map((item) => item.hue);
  const usedCandidateIndexes = new Set<number>();
  const themes = new Map<string, CategoryTheme>();

  for (const categoryId of ids) {
    const knownPalette = KNOWN_CATEGORY_PALETTE[categoryId];

    if (knownPalette) {
      themes.set(categoryId, buildCategoryTheme(knownPalette));
    }
  }

  for (const categoryId of ids) {
    if (KNOWN_CATEGORY_PALETTE[categoryId]) {
      continue;
    }

    const palette = resolveGeneratedPalette(
      categoryId,
      usedHues,
      usedCandidateIndexes,
    );
    themes.set(categoryId, buildCategoryTheme(palette));
    usedHues.push(palette.hue);

    if (typeof palette.candidateIndex === "number") {
      usedCandidateIndexes.add(palette.candidateIndex);
    }
  }

  return themes;
};

interface IndexedCategory extends DatasetCategory {
  _displayIndex: number;
}

const sortCategoriesForDisplay = (
  left: IndexedCategory,
  right: IndexedCategory,
) =>
  (left.sort ?? Number.MAX_SAFE_INTEGER) -
    (right.sort ?? Number.MAX_SAFE_INTEGER) ||
  left._displayIndex - right._displayIndex;

const dedupeIds = (ids: string[]): string[] => Array.from(new Set(ids));

const applySelectionLimit = (
  ids: string[],
  maxCount = MAX_SUBMIT_DATASET_COUNT,
): string[] => dedupeIds(ids).slice(0, Math.max(0, maxCount));

export const getCategoryTheme = (
  categoryId: string,
  categoryIds: readonly string[] = [categoryId],
): CategoryTheme => {
  const themeKey = normalizeCategoryThemeId(categoryId);
  return (
    getCategoryThemeMap([...categoryIds, themeKey]).get(themeKey) ??
    buildCategoryTheme({ hue: 220, saturation: 60, lightness: 45 })
  );
};

export const getEnabledCategories = (
  categories: DatasetCategory[],
): DatasetCategory[] =>
  categories
    .map((category, index) => ({
      ...category,
      _displayIndex: index,
    }))
    .filter((category) => category.enabled)
    .map((category) => {
      const enabledSubcategories = category.subcategories.filter(
        (item) => item.enabled,
      );

      return {
        ...category,
        subcategories: enabledSubcategories,
        subcategoryCount: enabledSubcategories.length,
      };
    })
    .filter((category) => category.subcategories.length > 0)
    .sort(sortCategoriesForDisplay)
    .map(({ _displayIndex, ...category }) => category);

export const getAllDatasetIds = (
  categories: DatasetCategory[],
  maxCount?: number,
): string[] => {
  const ids = getEnabledCategories(categories).flatMap((category) =>
    category.subcategories.map((item) => item.datasetId),
  );

  return typeof maxCount === "number"
    ? applySelectionLimit(ids, maxCount)
    : ids;
};

export const resolveActiveCategoryId = (
  categories: DatasetCategory[],
  preferredCategoryId?: string | null,
): string => {
  const enabledCategories = getEnabledCategories(categories);
  if (enabledCategories.length === 0) {
    return "";
  }

  if (
    preferredCategoryId &&
    enabledCategories.some(
      (category) => category.categoryId === preferredCategoryId,
    )
  ) {
    return preferredCategoryId;
  }

  return enabledCategories[0]?.categoryId ?? "";
};

export const findDatasetSummary = (
  categories: DatasetCategory[],
  datasetId: string,
): (DatasetSubcategory & { category: DatasetCategory }) | null => {
  for (const category of getEnabledCategories(categories)) {
    const dataset = category.subcategories.find(
      (item) => item.datasetId === datasetId,
    );

    if (dataset) {
      return {
        ...dataset,
        category,
      };
    }
  }

  return null;
};

export const sanitizeDatasetSelection = (
  categories: DatasetCategory[],
  selectedDatasetIds: string[],
  preserveEmptyInput = false,
  maxCount?: number,
): string[] => {
  const availableIds = new Set(getAllDatasetIds(categories));

  if (preserveEmptyInput && selectedDatasetIds.length === 0) {
    return [];
  }

  const sanitized = applySelectionLimit(
    selectedDatasetIds.filter((item) => availableIds.has(item)),
    maxCount ?? MAX_SUBMIT_DATASET_COUNT,
  );
  if (sanitized.length > 0) return sanitized;

  return typeof maxCount === "number"
    ? applySelectionLimit(Array.from(availableIds), maxCount)
    : Array.from(availableIds);
};

export const isCategoryFullySelected = (
  category: DatasetCategory,
  selectedDatasetIds: string[],
): boolean =>
  category.subcategories.every((item) =>
    selectedDatasetIds.includes(item.datasetId),
  );

export const toggleCategoryDatasets = (
  category: DatasetCategory,
  selectedDatasetIds: string[],
  maxCount = MAX_SUBMIT_DATASET_COUNT,
): string[] => {
  const datasetIds = category.subcategories.map((item) => item.datasetId);
  const fullySelected = datasetIds.every((item) =>
    selectedDatasetIds.includes(item),
  );

  if (fullySelected) {
    return selectedDatasetIds.filter((item) => !datasetIds.includes(item));
  }

  return applySelectionLimit([...selectedDatasetIds, ...datasetIds], maxCount);
};

export const toggleDatasetId = (
  datasetId: string,
  selectedDatasetIds: string[],
  maxCount = MAX_SUBMIT_DATASET_COUNT,
): string[] => {
  if (selectedDatasetIds.includes(datasetId)) {
    return selectedDatasetIds.filter((item) => item !== datasetId);
  }

  return applySelectionLimit([...selectedDatasetIds, datasetId], maxCount);
};

export const formatDateLabel = (value?: string): string => {
  if (!value) return translateRuntimeMessage("dataset.fallback.pending");

  return formatDateTime(value, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
};

export const formatDateTimeLabel = (value?: string): string => {
  if (!value) return translateRuntimeMessage("dataset.fallback.pending");

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
    return translateRuntimeMessage("dataset.fallback.pending");
  }
  return formatNumber(value);
};
