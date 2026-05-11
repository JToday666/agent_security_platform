import { defineStore } from "pinia";
import { ref } from "vue";
import type { SupportedLocale } from "@/app/i18n";

const INITIAL_LOCALE: SupportedLocale = "zh-CN";

export const useLocaleStore = defineStore("locale", () => {
  const displayLocale = ref<SupportedLocale>(INITIAL_LOCALE);
  const contentLocale = ref<SupportedLocale>(INITIAL_LOCALE);
  const loadedLocales = ref<SupportedLocale[]>([]);

  const setLocale = (locale: SupportedLocale) => {
    displayLocale.value = locale;
    contentLocale.value = locale;
  };

  const markLocaleLoaded = (locale: SupportedLocale) => {
    if (!loadedLocales.value.includes(locale)) {
      loadedLocales.value = [...loadedLocales.value, locale];
    }
  };

  return {
    contentLocale,
    displayLocale,
    loadedLocales,
    markLocaleLoaded,
    setLocale,
  };
});
