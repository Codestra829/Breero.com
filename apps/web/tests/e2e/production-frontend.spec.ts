import { expect, test } from "@playwright/test";

const routes = [
  "/",
  "/services",
  "/services/plumbing",
  "/how-it-works",
  "/about",
  "/contact",
  "/terms",
  "/privacy",
  "/refund-policy",
  "/cancellation-policy",
  "/service-fulfillment-policy",
  "/professional-lead-policy",
];

for (const route of routes) {
  test(`production frontend serves ${route}`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response?.status()).toBe(200);
    await expect(page.locator("main")).toBeVisible();
  });
}

test("book enters the canonical booking journey", async ({ page }) => {
  await page.goto("/book");
  await expect(page).toHaveURL(/\/booking$/);
  await expect(page.locator("main")).toBeVisible();
});

test("policy and contact surfaces expose the approved operator identity", async ({ page }) => {
  for (const route of ["/contact", "/terms", "/privacy", "/refund-policy", "/cancellation-policy", "/service-fulfillment-policy", "/professional-lead-policy"]) {
    await page.goto(route);
    await expect(page.getByText("Codestra LLC DBA Breero.com", { exact: false }).first()).toBeVisible();
    await expect(page.getByText("support@breero.com", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("20633 Longenbaugh Rd", { exact: false }).first()).toBeVisible();
  }
});
