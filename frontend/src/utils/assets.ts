const ABSOLUTE_URL_PATTERN = /^(?:[a-z]+:)?\/\//i;

const inferApiOrigin = (): string => {
  const apiBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (!apiBase || !ABSOLUTE_URL_PATTERN.test(apiBase)) {
    return "";
  }
  try {
    return new URL(apiBase).origin;
  } catch {
    return "";
  }
};

const trimTrailingSlash = (value: string): string => value.replace(/\/+$/, "");

export const resolveAssetUrl = (path?: string | null): string => {
  if (!path) {
    return "";
  }
  if (
    ABSOLUTE_URL_PATTERN.test(path) ||
    path.startsWith("data:") ||
    path.startsWith("blob:")
  ) {
    return path;
  }

  if (path.startsWith("/")) {
    const configuredAssetBase = import.meta.env.VITE_ASSET_BASE_URL as
      | string
      | undefined;
    const base = configuredAssetBase || inferApiOrigin();
    if (base) {
      return `${trimTrailingSlash(base)}${path}`;
    }
  }

  return path;
};
