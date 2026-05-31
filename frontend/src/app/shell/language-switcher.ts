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
