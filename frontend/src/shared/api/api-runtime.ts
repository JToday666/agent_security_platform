import { ApiConfig } from "@/shared/api/config";

export const isAbsoluteHttpUrl = (value: string): boolean =>
  /^https?:\/\//i.test(value);

const resolveApiOrigin = (baseUrl = ApiConfig.baseUrl): string | null => {
  if (!isAbsoluteHttpUrl(baseUrl)) {
    return null;
  }

  try {
    return new URL(baseUrl).origin;
  } catch {
    return null;
  }
};

export const normalizeApiAssetUrl = (
  value?: string | null,
  baseUrl = ApiConfig.baseUrl,
): string | null => {
  const normalizedValue = value?.trim();
  if (!normalizedValue) {
    return null;
  }

  if (isAbsoluteHttpUrl(normalizedValue)) {
    return normalizedValue;
  }

  const origin = resolveApiOrigin(baseUrl);
  if (!origin) {
    return normalizedValue;
  }

  if (normalizedValue.startsWith("/")) {
    return `${origin}${normalizedValue}`;
  }

  return `${origin}/${normalizedValue}`;
};
