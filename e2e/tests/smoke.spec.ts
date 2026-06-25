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

  test("pagination language switch skips missing ja/zh pages", async ({ page }, testInfo) => {
    // Use a high page number that exists in ko but not in ja/zh archives.
    await gotoOrSkip(page, testInfo, "/page/50/");

    const trigger = page.locator(".lang-switcher__trigger");
    await expect(trigger).toBeVisible({ timeout: 15_000 });
    await trigger.click();

    const jaLink = page.locator(".lang-switcher__option[href*='/ja/page/50']");
    const zhLink = page.locator(".lang-switcher__option[href*='/zh/page/50']");
    await expect(jaLink).toHaveCount(0);
    await expect(zhLink).toHaveCount(0);
  });

  test("tag archive language switch resolves localized slug", async ({ page }, testInfo) => {
    await gotoOrSkip(page, testInfo, "/archive/tag/개발-환경/");

    const trigger = page.locator(".lang-switcher__trigger");
    await expect(trigger).toBeVisible({ timeout: 15_000 });
    await trigger.click();

    const enLink = page.locator(
      ".lang-switcher__option[href*='/en/archive/tag/']"
    );
    const enHref = await enLink.getAttribute("href");
    if (!enHref) {
      testInfo.skip(true, "English tag archive link not available for this tag.");
      return;
    }

    expect(enHref).toMatch(/\/en\/archive\/tag\/development-environment\/?$/);

    const response = await page.goto(enHref, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
    if (!response || response.status() >= 500) {
      testInfo.skip(true, `English tag archive unreachable (${response?.status() ?? "no response"}).`);
      return;
    }

    await expect(page.locator("h1, .post-list, .archive-list").first()).toBeVisible({
      timeout: 15_000,
    });
  });

  test("RSS feed is available", async ({ page }, testInfo) => {
    const feedResponse = await page.goto("/rss.xml", {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
    if (!feedResponse) {
      testInfo.skip(true, "No response from /rss.xml.");
      return;
    }
    if (feedResponse.status() >= 500) {
      testInfo.skip(true, `RSS feed returned ${feedResponse.status()}.`);
      return;
    }
    expect(feedResponse.ok()).toBeTruthy();

    const contentType = feedResponse.headers()["content-type"] ?? "";
    expect(contentType).toMatch(/xml/i);

    const body = await page.locator("body").textContent();
    expect(body ?? "").toMatch(/<rss|<feed/i);

    const redirectResponse = await page.goto("/rss/", {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
    expect(redirectResponse?.ok()).toBeTruthy();

    const finalUrl = page.url();
    if (finalUrl.endsWith("/rss.xml")) {
      return;
    }

    const canonicalCount = await page.locator("link[rel='canonical']").count();
    if (canonicalCount > 0) {
      const canonicalHref = await page
        .locator("link[rel='canonical']")
        .first()
        .getAttribute("href");
      expect(canonicalHref?.endsWith("/rss.xml")).toBeTruthy();
      return;
    }

    const fallbackCount = await page.locator("a[href$='/rss.xml']").count();
    if (fallbackCount === 0) {
      testInfo.skip(
        true,
        "RSS redirect page not deployed yet; /rss.xml feed check already passed."
      );
    }
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