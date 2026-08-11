import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  outputDir: "./test-results",
  use: { baseURL: "http://127.0.0.1:3100", trace: "retain-on-failure" },
  webServer: { command: "pnpm exec next start -H 127.0.0.1 -p 3100", url: "http://127.0.0.1:3100", reuseExistingServer: true, timeout: 120_000 },
});
