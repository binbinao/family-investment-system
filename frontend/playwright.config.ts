import { defineConfig, devices } from "@playwright/test";

/**
 * 默认与 docker-compose 中 NEXT_PUBLIC_API_URL 使用同一 host（localhost），
 * 避免 127.0.0.1 与 localhost 混用导致 Cookie 不生效。
 * 纯前端 dev（无网关）时可设：PLAYWRIGHT_BASE_URL=http://127.0.0.1:3000
 */
const baseURL =
  process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:8888";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
