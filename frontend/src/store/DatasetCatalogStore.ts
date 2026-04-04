import { computed, ref } from "vue";
import { defineStore } from "pinia";
import {
  getDatasetCatalog,
  getDatasetDetail,
  type DatasetServiceError,
} from "@/api/DatasetService";
import type { DatasetCategory, DatasetDetail } from "@/types/DatasetTypes";
import {
  findDatasetSummary,
  getEnabledCategories,
  sanitizeCategorySelection,
} from "@/utils/common";
import { loadPersistedState, savePersistedState } from "@/utils/StorageUtils";
import { STORAGE_KEYS } from "@/constants/StorageKeys";

interface DatasetFilterPersistedData {
  selectedCategoryIds: string[];
}

const FILTER_STORAGE_VERSION = 1;

interface DatasetDetailFetchResult {
  detail: DatasetDetail | null;
  notFound: boolean;
  errorMessage: string;
}

export const useDatasetCatalogStore = defineStore("datasetCatalog", () => {
  const catalogVersion = ref("");
  const categories = ref<DatasetCategory[]>([]);
  const selectedCategoryIds = ref<string[]>([]);
  const loading = ref(false);
  const loaded = ref(false);
  const error = ref("");
  const detailCache = ref<Record<string, DatasetDetail>>({});
  const restoredFilterNotice = ref(false);

  const enabledCategories = computed(() =>
    getEnabledCategories(categories.value),
  );
  const visibleCategories = computed(() =>
    enabledCategories.value.filter((category) =>
      selectedCategoryIds.value.includes(category.categoryId),
    ),
  );

  const persistFilters = () => {
    savePersistedState<DatasetFilterPersistedData>(
      STORAGE_KEYS.catalog.filters,
      FILTER_STORAGE_VERSION,
      {
        selectedCategoryIds: selectedCategoryIds.value,
      },
      catalogVersion.value,
    );
  };

  const restoreFilters = () => {
    const persisted = loadPersistedState<DatasetFilterPersistedData>(
      STORAGE_KEYS.catalog.filters,
      FILTER_STORAGE_VERSION,
    );

    restoredFilterNotice.value = false;
    selectedCategoryIds.value = sanitizeCategorySelection(
      categories.value,
      persisted?.data.selectedCategoryIds ?? [],
      Boolean(persisted),
    );

    if (persisted?.data.selectedCategoryIds?.length) {
      restoredFilterNotice.value = true;
    }
  };

  const fetchCatalog = async (force = false): Promise<boolean> => {
    if (loaded.value && !force) return true;

    loading.value = true;
    error.value = "";

    try {
      const catalog = await getDatasetCatalog();
      catalogVersion.value = catalog.catalogVersion;
      categories.value = catalog.categories;
      loaded.value = true;
      restoreFilters();
      return true;
    } catch (fetchError) {
      error.value =
        fetchError instanceof Error
          ? fetchError.message
          : "目录加载失败，请稍后重试。";
      return false;
    } finally {
      loading.value = false;
    }
  };

  const selectAllCategories = () => {
    selectedCategoryIds.value = enabledCategories.value.map(
      (item) => item.categoryId,
    );
    persistFilters();
  };

  const clearAllCategories = () => {
    selectedCategoryIds.value = [];
    persistFilters();
  };

  const toggleCategorySelection = (categoryId: string) => {
    if (selectedCategoryIds.value.includes(categoryId)) {
      selectedCategoryIds.value = selectedCategoryIds.value.filter(
        (item) => item !== categoryId,
      );
    } else {
      selectedCategoryIds.value = [...selectedCategoryIds.value, categoryId];
    }

    persistFilters();
  };

  const fetchDatasetDetailById = async (
    datasetId: string,
    force = false,
  ): Promise<DatasetDetailFetchResult> => {
    if (detailCache.value[datasetId] && !force) {
      return {
        detail: detailCache.value[datasetId],
        notFound: false,
        errorMessage: "",
      };
    }

    try {
      const detail = await getDatasetDetail(datasetId);
      detailCache.value = {
        ...detailCache.value,
        [datasetId]: detail,
      };
      return {
        detail,
        notFound: false,
        errorMessage: "",
      };
    } catch (fetchError) {
      const error = fetchError as DatasetServiceError;
      return {
        detail: null,
        notFound: error.code === 40400,
        errorMessage:
          error.message ||
          (error.code === 40400
            ? "未找到对应评测项。"
            : "详情加载失败，请稍后重试。"),
      };
    }
  };

  const getDatasetSummaryById = (datasetId: string) =>
    findDatasetSummary(categories.value, datasetId);

  return {
    catalogVersion,
    categories,
    selectedCategoryIds,
    loading,
    loaded,
    error,
    enabledCategories,
    visibleCategories,
    restoredFilterNotice,
    fetchCatalog,
    selectAllCategories,
    clearAllCategories,
    toggleCategorySelection,
    fetchDatasetDetailById,
    getDatasetSummaryById,
  };
});
