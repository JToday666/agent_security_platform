// 通用的持久化状态管理 Composable
// 供 UserStore、SubmitDraftStore、DatasetCatalogStore 等复用

import { ref, computed, onMounted } from "vue";
import { loadPersistedState, savePersistedState } from "@/utils/StorageUtils";

export interface UsePersistentStoreOptions<T> {
  key: string;
  version: number;
  defaultValue: T;
  fetcher: () => Promise<T>;
  maxAge?: number;
}

export const usePersistentStore = <T>({
  key,
  version,
  defaultValue,
  fetcher,
  maxAge,
}: UsePersistentStoreOptions<T>) => {
  const data = ref<T>(defaultValue);
  const loading = ref(false);
  const loaded = ref(false);
  const error = ref("");

  const load = async (force = false): Promise<boolean> => {
    if (loaded.value && !force) return true;

    loading.value = true;
    error.value = "";

    try {
      data.value = await fetcher();
      loaded.value = true;
      savePersistedState(key, version, data.value);
      return true;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "加载失败";
      loaded.value = false;
      return false;
    } finally {
      loading.value = false;
    }
  };

  const restore = (): void => {
    const persisted = loadPersistedState<T>(key, version, maxAge);
    if (persisted?.data) {
      data.value = persisted.data;
      loaded.value = true;
    }
  };

  const refresh = (): Promise<boolean> => load(true);

  onMounted(() => restore());

  return {
    data: computed(() => data.value),
    loading: computed(() => loading.value),
    loaded: computed(() => loaded.value),
    error: computed(() => error.value),
    load,
    restore,
    refresh,
  };
};
