export interface ScrollPosition {
  left: number;
  top: number;
}

const SESSION_SCROLL_STORAGE_KEY_PREFIX = "agent-platform:session-scroll:v1";

interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

const normalizeScrollOffset = (value: unknown): number => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue) || numericValue <= 0) {
    return 0;
  }

  return Math.round(numericValue);
};

export const buildSessionScrollStorageKey = (
  routeName: string,
  params: Record<string, unknown> = {},
): string => {
  const normalizedParams = Object.entries(params)
    .filter(
      ([, value]) => value !== undefined && value !== null && value !== "",
    )
    .sort(([leftKey], [rightKey]) => leftKey.localeCompare(rightKey))
    .map(([key, value]) => `${key}=${String(value)}`)
    .join("&");

  return normalizedParams
    ? `${SESSION_SCROLL_STORAGE_KEY_PREFIX}::${routeName}::${normalizedParams}`
    : `${SESSION_SCROLL_STORAGE_KEY_PREFIX}::${routeName}`;
};

export const saveSessionScrollPosition = (
  storage: StorageLike,
  key: string,
  top: number,
): void => {
  const payload: ScrollPosition = {
    left: 0,
    top: normalizeScrollOffset(top),
  };

  storage.setItem(key, JSON.stringify(payload));
};

export const loadSessionScrollPosition = (
  storage: StorageLike,
  key: string,
): ScrollPosition | null => {
  const rawValue = storage.getItem(key);
  if (!rawValue) {
    return null;
  }

  try {
    const payload = JSON.parse(rawValue) as Partial<ScrollPosition>;
    return {
      left: 0,
      top: normalizeScrollOffset(payload.top),
    };
  } catch {
    return null;
  }
};
