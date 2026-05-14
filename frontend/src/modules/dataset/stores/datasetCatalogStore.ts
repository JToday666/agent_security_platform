import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { getCurrentDisplayLocale } from "@/app/i18n";
import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import {
  getDatasetCatalog,
  getDatasetDetail,
  type DatasetServiceError,
} from "@/modules/dataset/api/dataset-api";
import { getErrorMessage } from "@/shared/composables/useAsyncState";
import type {
  DatasetCategory,
  DatasetDetail,
} from "@/shared/types/dataset-types";
import {
  findDatasetSummary,
  getEnabledCategories,
  resolveActiveCategoryId,
} from "@/modules/dataset/lib/dataset-utils";

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
  const loadedLocale = ref("");
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
    const locale = getCurrentDisplayLocale();
    if (loaded.value && loadedLocale.value === locale && !force) return true;

    loading.value = true;
    error.value = "";

    try {
      const catalog = await getDatasetCatalog({ force });
      catalogVersion.value = catalog.catalogVersion;
      categories.value = catalog.categories;
      activeCategoryId.value = resolveActiveCategoryId(
        catalog.categories,
        activeCategoryId.value,
      );
      loaded.value = true;
      loadedLocale.value = locale;
      return true;
    } catch (fetchError) {
      error.value =
        getErrorMessage(
          fetchError,
          translateRuntimeMessage("dataset.api.catalogLoadFailed"),
        );
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
    const cacheKey = `${getCurrentDisplayLocale()}:${datasetId}`;

    if (detailCache.value[cacheKey] && !force) {
      return {
        detail: detailCache.value[cacheKey],
        notFound: false,
        errorMessage: "",
      };
    }

    try {
      const detail = await getDatasetDetail(datasetId, { force });
      detailCache.value = {
        ...detailCache.value,
        [cacheKey]: detail,
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
            ? translateRuntimeMessage("dataset.api.notFound")
            : translateRuntimeMessage("dataset.api.detailLoadFailed")),
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
