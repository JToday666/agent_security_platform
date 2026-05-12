import { translateRuntimeMessage } from "@/app/i18n/runtime-translator";
import { computed, ref } from "vue";
import { getDatasetCatalog } from "@/modules/dataset/api/dataset-api";
import type { DatasetCatalogResponse } from "@/shared/types/dataset-types";
import {
  getAllDatasetIds,
  getEnabledCategories,
} from "@/modules/dataset/lib/dataset-utils";

export type SubmitDatasetCatalogStatus =
  | "idle"
  | "loading"
  | "refreshing"
  | "ready"
  | "empty"
  | "error";

interface FetchCatalogOptions {
  signal?: AbortSignal;
  force?: boolean;
}

export const useSubmitDatasetCatalog = () => {
  const catalog = ref<DatasetCatalogResponse | null>(null);
  const status = ref<SubmitDatasetCatalogStatus>("idle");
  const errorMessage = ref("");

  const enabledCategories = computed(() =>
    getEnabledCategories(catalog.value?.categories ?? []),
  );

  const datasetIds = computed(() =>
    getAllDatasetIds(catalog.value?.categories ?? []),
  );
  const applyCatalog = (nextCatalog: DatasetCatalogResponse) => {
    catalog.value = nextCatalog;
    errorMessage.value = "";
    status.value = nextCatalog.subcategoryCount > 0 ? "ready" : "empty";
  };

  const fetchCatalog = async (
    options: FetchCatalogOptions = {},
  ): Promise<DatasetCatalogResponse> => {
    if (!options.force && catalog.value) {
      applyCatalog(catalog.value);
      return catalog.value;
    }

    const hasResolvedCatalog = Boolean(catalog.value);
    status.value = hasResolvedCatalog ? "refreshing" : "loading";
    errorMessage.value = "";

    try {
      const nextCatalog = await getDatasetCatalog({
        signal: options.signal,
        force: options.force,
      });

      applyCatalog(nextCatalog);
      return nextCatalog;
    } catch (error) {
      status.value = "error";
      errorMessage.value =
        error instanceof Error
          ? error.message
          : translateRuntimeMessage("submission.errors.catalogLoadFailed");
      throw error;
    }
  };

  return {
    catalog,
    status,
    errorMessage,
    enabledCategories,
    datasetIds,
    fetchCatalog,
  };
};
