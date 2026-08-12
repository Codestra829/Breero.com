import { expect, test } from "@playwright/test";
for (const width of [375, 430, 768, 1024, 1280, 1440])
  test(`homepage and booking entry fit ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /home services, without the hassle/i }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth <=
          document.documentElement.clientWidth,
      ),
    ).toBe(true);
    await page.goto("/booking?service=cleaning");
    await expect(
      page.getByRole("heading", { name: /what can we help/i }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth <=
          document.documentElement.clientWidth,
      ),
    ).toBe(true);
  });
test("booking happy path reaches authoritative pending confirmation", async ({
  page,
}) => {
  await page.goto("/booking?service=cleaning");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByLabel("Full address").fill("24 Lindenstraße, Berlin");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByLabel("Standard clean").check();
  await page.getByLabel("How many rooms?").fill("3");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.locator('input[name="slot"]').first().check();
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByLabel("First name").fill("Ada");
  await page.getByLabel("Last name").fill("Lovelace");
  await page.getByLabel("Email").fill("ada@example.com");
  await page.getByLabel("Phone").fill("+4912345");
  await page.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByRole("button", { name: "Submit booking" }).click();
  await page.getByRole("button", { name: "Continue to payment" }).click();
  await expect(
    page.getByRole("heading", { name: /confirming your booking/i }),
  ).toBeVisible();
  await expect(page.getByText(/Current status: requires_action/)).toBeVisible();
});
test("service-area failure remains recoverable", async ({ page }) => {
  await page.goto("/booking?service=cleaning");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByLabel("Full address").fill("Outside area");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.locator("p[role=alert]")).toContainText(
    "does not currently serve",
  );
});
