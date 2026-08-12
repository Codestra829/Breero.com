import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

for (const path of ["/", "/services", "/booking", "/login", "/account"]) {
  test(`${path} has no serious automated accessibility violations`, async ({ page }) => {
    await page.goto(path);
    await expect(page.locator("main")).toBeVisible();
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    expect(result.violations.filter((item) => ["serious", "critical"].includes(item.impact ?? ""))).toEqual([]);
  });
}
