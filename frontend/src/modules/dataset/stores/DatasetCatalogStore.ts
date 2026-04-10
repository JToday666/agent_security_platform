import { computed, ref } from "vue";
import { defineStore } from "pinia";
import {
  getDatasetCatalog,
  getDatasetDetail,
  type DatasetServiceError,
} from "@/modules/dataset/api/DatasetService";
import type {
  DatasetCategory,
  DatasetDetail,
} from "@/shared/types/DatasetTypes";
import {
  findDatasetSummary,
  getEnabledCategories,
  resolveActiveCategoryId,
} from "@/modules/dataset/lib";

interface DatasetDetailFetchResult {
  detail: DatasetDetail | null;
  notFound: boolean;
  errorMessage: string;
}

export const useDatasetCatalogStore = defineStore("datasetCatalog", () => {
  const catalogVersion = ref("");
  const categories = ref<DatasetCategory[]>([]);
  const activeCategoryId = ref("");
  const loading = ref(false);
  const loaded = ref(false);
  const error = ref("");
  const detailCache = ref<Record<string, DatasetDetail>>({});

  const enabledCategories = computed(() =>
    getEnabledCategories(categories.value),
  );
  const activeCategory = computed(
    () =>
      enabledCategories.value.find(
        (category) => category.categoryId === activeCategoryId.value,
      ) ??
      enabledCategories.value[0] ??
      null,
  );

  const fetchCatalog = async (force = false): Promise<boolean> => {
    if (loaded.value && !force) return true;

    loading.value = true;
    error.value = "";

    try {
      const catalog = await getDatasetCatalog();
      catalogVersion.value = catalog.catalogVersion;
      categories.value = catalog.categories;
      activeCategoryId.value = resolveActiveCategoryId(
        catalog.categories,
        activeCategoryId.value,
      );
      loaded.value = true;
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

  const setActiveCategory = (categoryId: string) => {
    activeCategoryId.value = resolveActiveCategoryId(
      categories.value,
      categoryId,
    );
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
    activeCategoryId,
    loading,
    loaded,
    error,
    enabledCategories,
    activeCategory,
    fetchCatalog,
    setActiveCategory,
    fetchDatasetDetailById,
    getDatasetSummaryById,
  };
});
