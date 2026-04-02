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

// ============ 持久化状态管理 ============

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

// ============ 通用本地存储操作 ============

export const setLocalStorage = (key: string, value: unknown): void => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Failed to set localStorage[${key}]:`, error);
  }
};

export const getLocalStorage = <T = unknown>(
  key: string,
  defaultValue?: T,
): T | null => {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return defaultValue ?? null;
    return JSON.parse(raw) as T;
  } catch (error) {
    console.error(`Failed to get localStorage[${key}]:`, error);
    return defaultValue ?? null;
  }
};

export const removeLocalStorage = (key: string): void => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Failed to remove localStorage[${key}]:`, error);
  }
};
