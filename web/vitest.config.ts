import path from "node:path";

import react from "@vitejs/plugin-react";
import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    // web/e2e/**/*.spec.ts holds Playwright specs (run via `npm run e2e`,
    // not vitest) - Playwright's `test`/`expect` aren't vitest's, so
    // letting vitest's default include glob pick them up would break them.
    exclude: [...configDefaults.exclude, "e2e/**"],
  },
});
