export const appendCacheBustParam = (
  url?: string | null,
  cacheBust?: string | number | null,
): string => {
  const normalizedUrl = url?.trim();
  if (!normalizedUrl) {
    return "";
  }

  if (cacheBust === undefined || cacheBust === null || cacheBust === "") {
    return normalizedUrl;
  }

  const separator = normalizedUrl.includes("?") ? "&" : "?";
  return `${normalizedUrl}${separator}v=${encodeURIComponent(String(cacheBust))}`;
};
