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
}

const CATEGORY_THEME_PALETTES: Array<
  [
    soft: string,
    solid: string,
    border: string,
    text: string,
    gradientStart: string,
    gradientEnd: string,
  ]
> = [
  ["#eff6ff", "#2563eb", "#93c5fd", "#1d4ed8", "#2563eb", "#60a5fa"],
  ["#eef2ff", "#4f46e5", "#a5b4fc", "#3730a3", "#4338ca", "#818cf8"],
  ["#f5f3ff", "#7c3aed", "#c4b5fd", "#6d28d9", "#7c3aed", "#a78bfa"],
  ["#faf5ff", "#9333ea", "#d8b4fe", "#7e22ce", "#9333ea", "#c084fc"],
  ["#fdf4ff", "#c026d3", "#f0abfc", "#a21caf", "#c026d3", "#e879f9"],
  ["#fdf2f8", "#db2777", "#f9a8d4", "#be185d", "#db2777", "#f472b6"],
  ["#fff1f2", "#e11d48", "#fda4af", "#be123c", "#e11d48", "#fb7185"],
  ["#fef2f2", "#dc2626", "#fca5a5", "#b91c1c", "#dc2626", "#f87171"],
  ["#fff7ed", "#ea580c", "#fdba74", "#c2410c", "#ea580c", "#fb923c"],
  ["#fffbeb", "#d97706", "#fcd34d", "#b45309", "#d97706", "#fbbf24"],
  ["#fefce8", "#ca8a04", "#fde047", "#a16207", "#ca8a04", "#facc15"],
  ["#f7fee7", "#65a30d", "#bef264", "#4d7c0f", "#65a30d", "#a3e635"],
  ["#f0fdf4", "#16a34a", "#86efac", "#15803d", "#16a34a", "#4ade80"],
  ["#ecfdf5", "#059669", "#6ee7b7", "#047857", "#059669", "#34d399"],
  ["#f0fdfa", "#0d9488", "#5eead4", "#0f766e", "#0d9488", "#2dd4bf"],
  ["#ecfeff", "#0891b2", "#67e8f9", "#0e7490", "#0891b2", "#22d3ee"],
  ["#f0f9ff", "#0284c7", "#7dd3fc", "#0369a1", "#0284c7", "#38bdf8"],
  ["#eef8ff", "#2563eb", "#bfdbfe", "#1e40af", "#1d4ed8", "#38bdf8"],
  ["#faf5ff", "#a21caf", "#e9d5ff", "#86198f", "#a21caf", "#d946ef"],
  ["#fff7ed", "#c2410c", "#fdba74", "#9a3412", "#c2410c", "#f59e0b"],
];

const CATEGORY_THEMES: CategoryTheme[] = CATEGORY_THEME_PALETTES.map(
  ([soft, solid, border, text, gradientStart, gradientEnd]) => ({
    soft,
    solid,
    border,
    text,
    gradient: `linear-gradient(135deg, ${gradientStart}, ${gradientEnd})`,
  }),
);

const buildFallbackCategoryTheme = (themeIndex: number): CategoryTheme => {
  const hue = Math.round((themeIndex * 137.508) % 360);
  const endHue = (hue + 24) % 360;

  return {
    soft: `hsl(${hue} 85% 95%)`,
    solid: `hsl(${hue} 72% 48%)`,
    border: `hsl(${hue} 72% 78%)`,
    text: `hsl(${hue} 66% 30%)`,
    gradient: `linear-gradient(135deg, hsl(${hue} 72% 48%), hsl(${endHue} 78% 60%))`,
  };
};

const sortCategoriesForDisplay = (
  left: DatasetCategory,
  right: DatasetCategory,
) => left.sort - right.sort || left.categoryId.localeCompare(right.categoryId);

// 主题色不再按 categoryId 哈希，而是按稳定排序后的索引分配。
export const getCategoryThemeByIndex = (themeIndex: number): CategoryTheme =>
  CATEGORY_THEMES[themeIndex] ?? buildFallbackCategoryTheme(themeIndex);

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
    .sort(sortCategoriesForDisplay)
    .map((category, themeIndex) => ({
      ...category,
      themeIndex,
    }));

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
