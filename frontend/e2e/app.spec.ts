import { test, expect } from "@playwright/test";

async function loginAsAdmin(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.locator("#username").fill("admin");
  await page.locator("#password").fill("admin123");
  await page.getByRole("button", { name: "登录" }).click();
  await page.waitForURL((u) => u.pathname === "/" || u.pathname === "", {
    timeout: 30_000,
  });
  await expect(page.getByRole("heading", { name: "家庭资产总览" })).toBeVisible({
    timeout: 25_000,
  });
}

test.describe("齐家 · 全功能端到端", () => {
  test("未登录访问受保护页会跳到登录", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: "齐家" })).toBeVisible();
  });

  test("登录后可依次打开全部主要功能页且无致命错误", async ({ page }) => {
    await loginAsAdmin(page);

    const routes: { path: string; heading: string | RegExp }[] = [
      { path: "/", heading: "家庭资产总览" },
      { path: "/trade", heading: "记账" },
      { path: "/ai", heading: /AI.*财务顾问|财务顾问/ },
      { path: "/reports", heading: "AI 晨报" },
      { path: "/memos", heading: "家庭备忘录" },
      { path: "/settings", heading: "系统设置" },
      { path: "/allocation", heading: "资产配置目标" },
      { path: "/history", heading: "交易历史" },
    ];

    for (const { path, heading } of routes) {
      await page.goto(path);
      await expect(page).toHaveURL(
        path === "/" ? /\/$/ : new RegExp(`${path.replace("/", "\\/")}$`),
        { timeout: 15_000 },
      );
      const locator =
        typeof heading === "string"
          ? page.getByRole("heading", { name: heading })
          : page.locator("h1").filter({ hasText: heading });
      await expect(locator.first()).toBeVisible({ timeout: 15_000 });
    }
  });

  test("主导航链接与总览、记账、AI 流程", async ({ page }) => {
    await loginAsAdmin(page);

    await page.getByRole("link", { name: "记账" }).click();
    await expect(page).toHaveURL(/\/trade$/);
    await expect(page.getByRole("heading", { name: "记账" })).toBeVisible();

    await page.getByRole("link", { name: "总览" }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("heading", { name: "家庭资产总览" })).toBeVisible();

    await page.locator('header a[href="/ai"]').click();
    await expect(page).toHaveURL(/\/ai$/);
    await expect(page.locator("h1")).toContainText(/财务顾问|AI/);
  });

  test("Phase2：总览资产走势与行情刷新；记账 Excel 导入 Tab", async ({ page }) => {
    await loginAsAdmin(page);
    await expect(page.getByText("资产走势")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole("button", { name: "刷新行情" })).toBeVisible();

    await page.goto("/trade");
    await expect(page.getByRole("heading", { name: "记账" })).toBeVisible();
    await page.getByRole("tab", { name: "Excel 导入" }).click();
    await expect(page.getByRole("button", { name: "下载持仓模板" })).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByRole("button", { name: "下载交易模板" })).toBeVisible();
  });
});
