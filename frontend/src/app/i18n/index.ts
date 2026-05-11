export const SUPPORTED_LOCALES = [
  "zh-CN",
  "en-US",
  "fr-FR",
  "es-ES",
  "ja-JP",
] as const;

export const DEFAULT_LOCALE = "zh-CN";

export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];
