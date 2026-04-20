import type {
  DatasetCategory,
  DatasetCategoryViewModel,
  DatasetSubcategory,
} from "@/shared/types/dataset-types";
import { ORDERED_REFERENCE_CATEGORY_IDS } from "@/modules/dataset/model/dataset-taxonomy";
import { MAX_SUBMIT_DATASET_COUNT } from "@/modules/submission/model/parameter-validator";

export interface CategoryTheme {
  soft: string;
  solid: string;
  border: string;
  text: string;
  gradient: string;
  shadow: string;
}

const COMFORT_HUE_ANCHORS = [162, 192, 220, 244, 270, 24, 340] as const;
const MIN_HUE_GAP = 22;
const HUE_JITTER_RANGE = 5;
const ACCENT_HUE_OFFSET = 7;

const CATEGORY_THEME_CACHE = new Map<string, CategoryTheme>();
const REFERENCE_CATEGORY_ORDER = new Map(
  ORDERED_REFERENCE_CATEGORY_IDS.map((categoryId, index) => [
    categoryId,
    index,
  ]),
);

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
  (REFERENCE_CATEGORY_ORDER.get(left) ?? Number.MAX_SAFE_INTEGER) -
    (REFERENCE_CATEGORY_ORDER.get(right) ?? Number.MAX_SAFE_INTEGER) ||
  left.localeCompare(right);

const getHueDistance = (left: number, right: number): number => {
  const delta = Math.abs(normalizeHue(left - right));
  return delta > 180 ? 360 - delta : delta;
};

const ensureMinimumHueGap = (hue: number, usedHues: number[]): number => {
  let resolvedHue = normalizeHue(hue);

  for (let attempt = 0; attempt < 12; attempt += 1) {
    const hasConflict = usedHues.some(
      (item) => getHueDistance(resolvedHue, item) < MIN_HUE_GAP,
    );

    if (!hasConflict) {
      return resolvedHue;
    }

    resolvedHue = normalizeHue(resolvedHue + MIN_HUE_GAP / 2);
  }

  return resolvedHue;
};

const buildResolvedHueMap = (
  categoryIds: readonly string[],
): Map<string, number> => {
  const ids = Array.from(
    new Set(categoryIds.map((item) => item.trim()).filter(Boolean)),
  ).sort(compareCategoryIds);

  if (ids.length === 0) {
    return new Map();
  }

  const collectionSeed = ids.reduce(
    (seed, categoryId) => mixHash(seed ^ hashCategoryId(categoryId)),
    2166136261,
  );
  const anchorRotation = collectionSeed % COMFORT_HUE_ANCHORS.length;

  const rankedIds = ids
    .map((categoryId) => ({
      categoryId,
      score: mixHash(hashCategoryId(categoryId)) / 0x100000000,
      jitterSeed: mixHash(hashCategoryId(`${categoryId}:hue-jitter`)),
    }))
    .sort(
      (left, right) =>
        left.score - right.score ||
        compareCategoryIds(left.categoryId, right.categoryId),
    );

  const usedHues: number[] = [];
  const resolvedEntries = rankedIds.map((item, index) => {
    const anchor =
      COMFORT_HUE_ANCHORS[
        (index + anchorRotation) % COMFORT_HUE_ANCHORS.length
      ]!;
    const jitter = ((item.jitterSeed / 0x100000000) * 2 - 1) * HUE_JITTER_RANGE;
    const baseHue = ensureMinimumHueGap(anchor + jitter, usedHues);
    usedHues.push(baseHue);

    return [item.categoryId, baseHue] as const;
  });

  return new Map(resolvedEntries);
};

const REFERENCE_CATEGORY_HUES = buildResolvedHueMap(
  ORDERED_REFERENCE_CATEGORY_IDS,
);

const resolveBaseHue = (categoryId: string): number =>
  REFERENCE_CATEGORY_HUES.get(categoryId) ??
  buildResolvedHueMap([...ORDERED_REFERENCE_CATEGORY_IDS, categoryId]).get(
    categoryId,
  )!;

const buildCategoryTheme = (categoryId: string): CategoryTheme => {
  const baseHue = resolveBaseHue(categoryId);
  const accentHue = normalizeHue(baseHue + ACCENT_HUE_OFFSET);

  return {
    soft: toHsl(baseHue, 64, 97),
    solid: toHsl(baseHue, 60, 43),
    border: toHsl(baseHue, 52, 86),
    text: toHsl(baseHue, 38, 30),
    gradient: `linear-gradient(135deg, ${toHsl(baseHue, 58, 42)}, ${toHsl(accentHue, 56, 48)})`,
    shadow: toHsla(baseHue, 36, 40, 0.16),
  };
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

export const getCategoryTheme = (categoryId: string): CategoryTheme => {
  const themeKey = categoryId.trim() || "__default__";
  const cachedTheme = CATEGORY_THEME_CACHE.get(themeKey);

  if (cachedTheme) {
    return cachedTheme;
  }

  const theme = buildCategoryTheme(themeKey);
  CATEGORY_THEME_CACHE.set(themeKey, theme);
  return theme;
};

export const getEnabledCategories = (
  categories: DatasetCategory[],
): DatasetCategoryViewModel[] =>
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
): (DatasetSubcategory & { category: DatasetCategoryViewModel }) | null => {
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
  if (!value) return "待补充";

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
};

export const formatDateTimeLabel = (value?: string): string => {
  if (!value) return "待补充";

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
};

export const formatSampleCount = (value?: number): string => {
  if (typeof value !== "number") return "待补充";
  return new Intl.NumberFormat("zh-CN").format(value);
};
