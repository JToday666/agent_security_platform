export type TranslateParams = Record<
  string,
  string | number | boolean | null | undefined
>;

export type AppTranslator = (key: string, params?: TranslateParams) => string;

let hasWarnedDefaultTranslator = false;

const defaultRuntimeTranslator: AppTranslator = (key) => {
  if (import.meta.env.DEV && !hasWarnedDefaultTranslator) {
    hasWarnedDefaultTranslator = true;
    console.warn(
      "[runtime-translator] i18n runtime translator is not installed; returning message keys.",
    );
  }

  return key;
};

let runtimeTranslator: AppTranslator = defaultRuntimeTranslator;

export const setRuntimeTranslator = (translator: AppTranslator) => {
  runtimeTranslator = translator;
};

export const resetRuntimeTranslator = () => {
  hasWarnedDefaultTranslator = false;
  runtimeTranslator = defaultRuntimeTranslator;
};

export const translateRuntimeMessage: AppTranslator = (key, params) =>
  runtimeTranslator(key, params);
