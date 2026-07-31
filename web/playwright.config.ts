import { defineConfig } from "@playwright/test";

// End-to-end smoke test for the demo path (Task 7.6). Boots two servers:
//   1. The FastAPI backend, pointed at a throwaway sqlite file and with
//      RESEARCHFORGE_DEV_SEED=1 so POST /api/dev/seed is available. This
//      seeds a fixed project instead of running the real Claude pipeline.
//   2. The Next.js dev server, which proxies /api/* to the backend (see
//      next.config.mjs).
//
// See web/e2e/report_flow.spec.ts for the spec itself, and
// api/app/routes/dev.py for the seed route.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    // This sandbox's macOS version is too old for Playwright's bundled
    // Chromium build ("does not support chromium on mac13-arm64"), so
    // drive the system-installed Google Chrome instead of downloading one.
    // Locally on a supported OS, `npx playwright install chromium` plus
    // dropping this line works too.
    channel: "chrome",
  },
  webServer: [
    {
      command:
        "cd ../api && RESEARCHFORGE_DEV_SEED=1 DATABASE_URL=sqlite:///./e2e.db .venv/bin/python -m uvicorn app.main:app --port 8000",
      url: "http://localhost:8000/api/health",
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run dev",
      url: "http://localhost:3000",
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
