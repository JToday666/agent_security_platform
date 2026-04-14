interface CacheEntry<T> {
  value: T;
  expiresAt: number | null;
}

interface ReadMemoryCacheOptions {
  now?: number;
}

interface MemoryCacheOptions extends ReadMemoryCacheOptions {
  force?: boolean;
  ttlMs?: number;
}

const valueCache = new Map<string, CacheEntry<unknown>>();
const inflightCache = new Map<string, Promise<unknown>>();

const isEntryExpired = (
  entry: CacheEntry<unknown>,
  now = Date.now(),
): boolean => entry.expiresAt !== null && entry.expiresAt <= now;

export const readMemoryCache = <T>(
  key: string,
  options: ReadMemoryCacheOptions = {},
): T | undefined => {
  const entry = valueCache.get(key);
  if (!entry) {
    return undefined;
  }

  if (isEntryExpired(entry, options.now)) {
    valueCache.delete(key);
    return undefined;
  }

  return entry.value as T;
};

export const setMemoryCache = <T>(key: string, value: T, ttlMs?: number): T => {
  valueCache.set(key, {
    value,
    expiresAt:
      typeof ttlMs === "number" && ttlMs > 0 ? Date.now() + ttlMs : null,
  });
  return value;
};

export const withMemoryCache = async <T>(
  key: string,
  loader: () => Promise<T>,
  options: MemoryCacheOptions = {},
): Promise<T> => {
  if (!options.force) {
    const cachedValue = readMemoryCache<T>(key, options);
    if (cachedValue !== undefined) {
      return cachedValue;
    }

    const inflightPromise = inflightCache.get(key);
    if (inflightPromise) {
      return inflightPromise as Promise<T>;
    }
  }

  const nextPromise = loader()
    .then((value) => setMemoryCache(key, value, options.ttlMs))
    .finally(() => {
      inflightCache.delete(key);
    });

  inflightCache.set(key, nextPromise as Promise<unknown>);
  return nextPromise;
};
