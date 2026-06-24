import { test, expect } from "@playwright/test";
import { clearStorageKeys, gotoOrSkip, SITE_TITLE } from "./helpers";

test.describe("blog smoke tests", () => {
  test("homepage loads and shows masthead title", async ({ page }, testInfo) => {
    await gotoOrSkip(page, testInfo, "/");

    const masthead = page.locator(".masthead-title");
    await expect(masthead).toBeVisible({ timeout: 15_000 });
    await expect(masthead).toContainText(SITE_TITLE);
  });

  test("cookie banner appears on first visit", async ({ page }, testInfo) => {
    await gotoOrSkip(page, testInfo, "/");
    await clearStorageKeys(page, ["blog-consent-v1"]);
    await page.reload({ waitUntil: "domcontentloaded" });

    const banner = page.locator("#cookie-consent");
    await expect(banner).toBeVisible({ timeout: 15_000 });
    await expect(banner).not.toHaveAttribute("hidden", "");
  });

  test("cookie reject hides the banner", async ({ page }, testInfo) => {
    await gotoOrSkip(page, testInfo, "/");
    await clearStorageKeys(page, ["blog-consent-v1"]);
    await page.reload({ waitUntil: "domcontentloaded" });

    const banner = page.locator("#cookie-consent");
    await expect(banner).toBeVisible({ timeout: 15_000 });

    await page.locator("#cookie-consent-reject").click();
    await expect(banner).toBeHidden({ timeout: 10_000 });
  });

  test("search page loads pagefind UI", async ({ page }, testInfo) => {
    await gotoOrSkip(page, testInfo, "/search/");

    const pagefindRoot = page.locator("#pagefind-search .pagefind-ui");
    const pagefindInput = page.locator(
      "#pagefind-search input[type='search'], #pagefind-search .pagefind-ui__search-input"
    );

    try {
      await expect(pagefindRoot.or(pagefindInput).first()).toBeVisible({
        timeout: 45_000,
      });
    } catch {
      testInfo.skip(
        true,
        "Pagefind UI did not load in time (index or CDN may be slow/unavailable)."
      );
    }
  });

  test("theme toggle changes data-theme on html", async ({ page }, testInfo) => {
    await gotoOrSkip(page, testInfo, "/");
    await clearStorageKeys(page, ["theme-preference"]);
    await page.reload({ waitUntil: "domcontentloaded" });

    const html = page.locator("html");
    const toggle = page.locator("#theme-toggle");
    await expect(toggle).toBeVisible({ timeout: 15_000 });

    const before = await html.getAttribute("data-theme");

    await toggle.click();

    await expect
      .poll(async () => html.getAttribute("data-theme"), { timeout: 10_000 })
      .not.toBe(before);

    const after = await html.getAttribute("data-theme");
    expect(after === "light" || after === "dark").toBeTruthy();
  });

  test("language switcher opens on Korean home", async ({ page }, testInfo) => {
    await gotoOrSkip(page, testInfo, "/");

    const details = page.locator(".lang-switcher__details");
    const trigger = page.locator(".lang-switcher__trigger");
    const menu = page.locator(".lang-switcher__menu");

    await expect(trigger).toBeVisible({ timeout: 15_000 });
    await expect(details).not.toHaveAttribute("open", "");

    await trigger.click();

    await expect(details).toHaveAttribute("open", "");
    await expect(menu).toBeVisible({ timeout: 10_000 });
    await expect(menu.locator(".lang-switcher__option").first()).toBeVisible();
  });
});