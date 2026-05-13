import type { SupportedLocale } from "@/app/i18n";

export interface LanguageOption {
  locale: SupportedLocale;
  nativeLabel: string;
}

export const LANGUAGE_OPTIONS: LanguageOption[] = [
  { locale: "zh-CN", nativeLabel: "汉语" },
  { locale: "en-US", nativeLabel: "English" },
  { locale: "fr-FR", nativeLabel: "Français" },
  { locale: "es-ES", nativeLabel: "Español" },
  { locale: "ja-JP", nativeLabel: "日本語" },
];

export const getLanguageOption = (locale: SupportedLocale): LanguageOption =>
  LANGUAGE_OPTIONS.find((option) => option.locale === locale) ??
  LANGUAGE_OPTIONS[0];

export const getNativeLanguageLabel = (locale: SupportedLocale): string =>
  getLanguageOption(locale).nativeLabel;
