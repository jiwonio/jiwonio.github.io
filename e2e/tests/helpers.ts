import { Page, TestInfo } from "@playwright/test";

const SITE_TITLE = "Jiwon Min";

export async function gotoOrSkip(
  page: Page,
  testInfo: TestInfo,
  path = "/"
): Promise<void> {
  try {
    const response = await page.goto(path, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });

    if (!response) {
      testInfo.skip(true, "No response from site (external site may be down).");
      return;
    }

    if (response.status() >= 500) {
      testInfo.skip(
        true,
        `Site returned ${response.status()} (external site may be down).`
      );
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    testInfo.skip(true, `Site unreachable: ${message}`);
  }
}

export async function clearStorageKeys(
  page: Page,
  keys: string[]
): Promise<void> {
  await page.evaluate((storageKeys) => {
    for (const key of storageKeys) {
      localStorage.removeItem(key);
    }
  }, keys);
}

export { SITE_TITLE };