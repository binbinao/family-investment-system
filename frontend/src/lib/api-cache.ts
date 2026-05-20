/**
 * Frontend API response cache with TTL.
 * Reduces duplicate requests for data that doesn't change frequently.
 *
 * Usage:
 *   const data = await cachedFetch("dashboard-summary", () => api.dashboard.summary(), 120_000);
 */

const cache = new Map<string, { data: unknown; expireAt: number }>();

/**
 * Fetch with in-memory cache.
 * @param key    Cache key (unique per data source)
 * @param fetcher  Async function that fetches the data
 * @param ttl    Time-to-live in milliseconds (default 5 min)
 */
export async function cachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl = 300_000,
): Promise<T> {
  const cached = cache.get(key);
  if (cached && Date.now() < cached.expireAt) {
    return cached.data as T;
  }
  const data = await fetcher();
  cache.set(key, { data, expireAt: Date.now() + ttl });
  return data;
}

/** Invalidate a specific cache key. */
export function invalidateCache(key: string): void {
  cache.delete(key);
}

/** Invalidate all cache entries matching a prefix. */
export function invalidateCachePrefix(prefix: string): void {
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) {
      cache.delete(key);
    }
  }
}

/** Clear the entire cache. */
export function clearCache(): void {
  cache.clear();
}

/** Recommended TTLs by data type */
export const CACHE_TTL = {
  MARKET_DATA: 5 * 60 * 1000,     // 5 min
  DASHBOARD: 2 * 60 * 1000,       // 2 min
  HOLDINGS: 60 * 1000,            // 1 min
  AI_CHAT: 0,                      // no cache
} as const;
