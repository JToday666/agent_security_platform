import { computed, ref } from "vue";
import { getDatasetCatalog } from "@/api/DatasetService";
import type {
  DatasetCatalogResponse,
  DatasetCategoryViewModel,
} from "@/types/DatasetTypes";
import { getAllDatasetIds, getEnabledCategories } from "@/utils/DatasetUtils";

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

const difficultyKey = (difficulty: number): string => difficulty.toFixed(1);

export const useSubmitDatasetCatalog = () => {
  const catalog = ref<DatasetCatalogResponse | null>(null);
  const status = ref<SubmitDatasetCatalogStatus>("idle");
  const errorMessage = ref("");
  const cachedCatalogs = ref<Record<string, DatasetCatalogResponse>>({});
  const lastRequestedDifficultyKey = ref("");
  const resolvedDifficultyKey = ref("");

  const enabledCategories = computed<DatasetCategoryViewModel[]>(() =>
    getEnabledCategories(catalog.value?.categories ?? []),
  );

  const catalogVersion = computed(() => catalog.value?.catalogVersion ?? "");
  const datasetIds = computed(() =>
    getAllDatasetIds(catalog.value?.categories ?? []),
  );
  const hasResolvedCurrentDifficulty = computed(
    () => lastRequestedDifficultyKey.value === resolvedDifficultyKey.value,
  );

  const applyCatalog = (
    difficulty: number,
    nextCatalog: DatasetCatalogResponse,
  ) => {
    catalog.value = nextCatalog;
    resolvedDifficultyKey.value = difficultyKey(difficulty);
    errorMessage.value = "";
    status.value = nextCatalog.subcategoryCount > 0 ? "ready" : "empty";
  };

  const fetchCatalog = async (
    difficulty: number,
    options: FetchCatalogOptions = {},
  ): Promise<DatasetCatalogResponse> => {
    const key = difficultyKey(difficulty);
    lastRequestedDifficultyKey.value = key;

    if (!options.force && cachedCatalogs.value[key]) {
      const cached = cachedCatalogs.value[key];
      applyCatalog(difficulty, cached);
      return cached;
    }

    const hasResolvedCatalog = Boolean(resolvedDifficultyKey.value);
    status.value = hasResolvedCatalog ? "refreshing" : "loading";
    errorMessage.value = "";

    try {
      const nextCatalog = await getDatasetCatalog({
        difficulty,
        signal: options.signal,
      });

      cachedCatalogs.value = {
        ...cachedCatalogs.value,
        [key]: nextCatalog,
      };
      applyCatalog(difficulty, nextCatalog);
      return nextCatalog;
    } catch (error) {
      status.value = "error";
      errorMessage.value =
        error instanceof Error ? error.message : "目录加载失败，请重试。";
      throw error;
    }
  };

  return {
    catalog,
    catalogVersion,
    status,
    errorMessage,
    enabledCategories,
    datasetIds,
    lastRequestedDifficultyKey,
    resolvedDifficultyKey,
    hasResolvedCurrentDifficulty,
    fetchCatalog,
  };
};
