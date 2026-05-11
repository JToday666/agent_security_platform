import { getCurrentDisplayLocale, type SupportedLocale } from "@/app/i18n";

const resolveLocale = (locale?: SupportedLocale) =>
  locale ?? getCurrentDisplayLocale();

export const formatNumber = (
  value: number,
  options?: Intl.NumberFormatOptions,
  locale?: SupportedLocale,
): string => new Intl.NumberFormat(resolveLocale(locale), options).format(value);

export const formatDateTime = (
  value: Date | number | string,
  options?: Intl.DateTimeFormatOptions,
  locale?: SupportedLocale,
): string =>
  new Intl.DateTimeFormat(resolveLocale(locale), options).format(
    value instanceof Date ? value : new Date(value),
  );

export const formatPercent = (
  value: number,
  locale?: SupportedLocale,
): string =>
  formatNumber(value, {
    maximumFractionDigits: 1,
    style: "percent",
  }, locale);
