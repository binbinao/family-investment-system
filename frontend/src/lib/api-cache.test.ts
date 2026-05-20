import { describe, it, expect, vi, beforeEach } from "vitest";
import { cachedFetch, clearCache } from "@/lib/api-cache";

describe("api-cache", () => {
  beforeEach(() => {
    clearCache();
    vi.clearAllMocks();
  });

  it("calls fetcher on first request", async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: "test" });
    const result = await cachedFetch("key1", fetcher, 60000);
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(result).toEqual({ data: "test" });
  });

  it("returns cached data within TTL", async () => {
    const fetcher = vi.fn().mockResolvedValue({ data: "test" });
    await cachedFetch("key1", fetcher, 60000);
    const result = await cachedFetch("key1", fetcher, 60000);
    expect(fetcher).toHaveBeenCalledTimes(1); // not called again
    expect(result).toEqual({ data: "test" });
  });

  it("calls fetcher again after TTL expires", async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn().mockResolvedValue({ data: "test" });
    await cachedFetch("key1", fetcher, 1000); // 1s TTL
    vi.advanceTimersByTime(1500);
    await cachedFetch("key1", fetcher, 1000);
    expect(fetcher).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });

  it("clearCache removes all cached entries", async () => {
    const fetcher = vi.fn().mockResolvedValue("data");
    await cachedFetch("key1", fetcher, 60000);
    clearCache();
    await cachedFetch("key1", fetcher, 60000);
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});
