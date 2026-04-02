import type {
  DatasetCategory,
  DatasetCatalogResponse,
  DatasetCategoryViewModel,
  DatasetSubcategory,
} from "@/types/DatasetTypes";

export interface CategoryTheme {
  soft: string;
  solid: string;
  border: string;
  text: string;
  gradient: string;
  shadow: string;
}

const COMFORT_HUE_RANGES: ReadonlyArray<readonly [start: number, end: number]> = [
  [152, 178],
  [184, 208],
  [214, 232],
  [238, 258],
  [264, 286],
  [294, 318],
  [326, 348],
  [4, 26],
];

const CATEGORY_THEME_CACHE = new Map<string, CategoryTheme>();

const COMFORT_HUE_TOTAL = COMFORT_HUE_RANGES.reduce(
  (total, [start, end]) => total + (end - start),
  0,
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

const mapNormalizedValueToHue = (value: number): number => {
  let offset = value * COMFORT_HUE_TOTAL;

  for (const [start, end] of COMFORT_HUE_RANGES) {
    const span = end - start;

    if (offset < span) {
      return start + offset;
    }

    offset -= span;
  }

  const [lastStart, lastEnd] =
    COMFORT_HUE_RANGES[COMFORT_HUE_RANGES.length - 1]!;
  return lastEnd - Math.max(1, lastEnd - lastStart) / 2;
};

const buildCategoryTheme = (categoryId: string): CategoryTheme => {
  const hash = mixHash(hashCategoryId(categoryId));
  const normalizedBase = hash / 0x100000000;
  const normalizedAccent = (normalizedBase + 0.07) % 1;
  const baseHue = mapNormalizedValueToHue(normalizedBase);
  const accentHue = mapNormalizedValueToHue(normalizedAccent);

  return {
    soft: toHsl(baseHue, 64, 97),
    solid: toHsl(baseHue, 60, 43),
    border: toHsl(baseHue, 52, 86),
    text: toHsl(baseHue, 38, 30),
    gradient: `linear-gradient(135deg, ${toHsl(baseHue, 58, 42)}, ${toHsl(accentHue, 56, 48)})`,
    shadow: toHsla(baseHue, 36, 40, 0.16),
  };
};

const sortCategoriesForDisplay = (
  left: DatasetCategory,
  right: DatasetCategory,
) => left.sort - right.sort || left.categoryId.localeCompare(right.categoryId);

// 主题色不再按 categoryId 哈希，而是按稳定排序后的索引分配。
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
    .sort(sortCategoriesForDisplay);

export const getAllDatasetIds = (categories: DatasetCategory[]): string[] =>
  getEnabledCategories(categories).flatMap((category) =>
    category.subcategories.map((item) => item.datasetId),
  );

export const countVisibleDatasets = (
  categories: DatasetCategory[],
  selectedCategoryIds: string[],
): number =>
  getEnabledCategories(categories)
    .filter((category) => selectedCategoryIds.includes(category.categoryId))
    .reduce((total, category) => total + category.subcategories.length, 0);

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

export const sanitizeCategorySelection = (
  categories: DatasetCategory[],
  selectedCategoryIds: string[],
  preserveEmptyInput = false,
): string[] => {
  const availableIds = new Set(
    getEnabledCategories(categories).map((item) => item.categoryId),
  );

  if (preserveEmptyInput && selectedCategoryIds.length === 0) {
    return [];
  }

  const sanitized = selectedCategoryIds.filter((item) =>
    availableIds.has(item),
  );
  if (sanitized.length > 0) return sanitized;

  return Array.from(availableIds);
};

export const sanitizeDatasetSelection = (
  categories: DatasetCategory[],
  selectedDatasetIds: string[],
  preserveEmptyInput = false,
): string[] => {
  const availableIds = new Set(getAllDatasetIds(categories));

  if (preserveEmptyInput && selectedDatasetIds.length === 0) {
    return [];
  }

  const sanitized = selectedDatasetIds.filter((item) => availableIds.has(item));
  if (sanitized.length > 0) return sanitized;

  return Array.from(availableIds);
};

export const countSelectedDatasets = (
  categories: DatasetCategory[],
  selectedDatasetIds: string[],
): number => sanitizeDatasetSelection(categories, selectedDatasetIds).length;

export const isCategoryFullySelected = (
  category: DatasetCategory,
  selectedDatasetIds: string[],
): boolean =>
  category.subcategories.every((item) =>
    selectedDatasetIds.includes(item.datasetId),
  );

export const isCategoryPartiallySelected = (
  category: DatasetCategory,
  selectedDatasetIds: string[],
): boolean => {
  const selectedCount = category.subcategories.filter((item) =>
    selectedDatasetIds.includes(item.datasetId),
  ).length;

  return selectedCount > 0 && selectedCount < category.subcategories.length;
};

export const toggleCategoryDatasets = (
  category: DatasetCategory,
  selectedDatasetIds: string[],
): string[] => {
  const datasetIds = category.subcategories.map((item) => item.datasetId);
  const fullySelected = datasetIds.every((item) =>
    selectedDatasetIds.includes(item),
  );

  if (fullySelected) {
    return selectedDatasetIds.filter((item) => !datasetIds.includes(item));
  }

  return Array.from(new Set([...selectedDatasetIds, ...datasetIds]));
};

export const toggleDatasetId = (
  datasetId: string,
  selectedDatasetIds: string[],
): string[] => {
  if (selectedDatasetIds.includes(datasetId)) {
    return selectedDatasetIds.filter((item) => item !== datasetId);
  }

  return [...selectedDatasetIds, datasetId];
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

export const buildCatalogStats = (catalog: DatasetCatalogResponse | null) => ({
  categoryCount: catalog?.categoryCount ?? 0,
  subcategoryCount: catalog?.subcategoryCount ?? 0,
});
