import type { PersistedState } from "@/types/CommonTypes";

const DEFAULT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

// 本地存储读取失败时直接返回 null，避免历史脏数据中断页面初始化。
const parseJson = <T>(raw: string | null): T | null => {
  if (!raw) return null;

  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
};

export const loadPersistedState = <T>(
  key: string,
  version: number,
  maxAgeMs = DEFAULT_MAX_AGE_MS,
): PersistedState<T> | null => {
  const parsed = parseJson<PersistedState<T>>(localStorage.getItem(key));
  if (!parsed) return null;
  if (parsed.version !== version) return null;
  if (Date.now() - parsed.savedAt > maxAgeMs) return null;
  return parsed;
};

export const savePersistedState = <T>(
  key: string,
  version: number,
  data: T,
  catalogVersion?: string,
): void => {
  const payload: PersistedState<T> = {
    version,
    savedAt: Date.now(),
    catalogVersion,
    data,
  };

  localStorage.setItem(key, JSON.stringify(payload));
};

export const clearPersistedState = (key: string): void => {
  localStorage.removeItem(key);
};
