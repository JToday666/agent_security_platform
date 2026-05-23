import { computed, watch, type Ref, type WatchStopHandle } from "vue";
import { normalizeLocale } from "@/app/i18n";

export const useDatasetLocaleRefresh = (
  locale: Ref<string>,
  refresh: () => unknown | Promise<unknown>,
): WatchStopHandle => {
  const currentLocale = computed(() => normalizeLocale(locale.value));

  return watch(currentLocale, async (nextLocale, previousLocale) => {
    if (nextLocale === previousLocale) {
      return;
    }

    await refresh();
  });
};
