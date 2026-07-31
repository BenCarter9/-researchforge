import { expect, test } from "@playwright/test";

// End-to-end smoke test of the demo path (Task 7.6):
//   seed a fixed project -> open its report -> open a green claim's
//   citation and confirm the source viewer highlights the verbatim quote
//   -> switch to Financials and confirm a missing fact renders as
//   "unavailable" (never 0, never blank).
//
// The seed comes from POST /api/dev/seed (api/app/routes/dev.py), which is
// only registered when the API is started with RESEARCHFORGE_DEV_SEED=1
// (see web/playwright.config.ts's webServer command) - it never runs the
// real Claude pipeline.

const VERBATIM_QUOTE = "North American revenue increased 18% in FY2025";

test("demo path: seeded citation highlights and financials show unavailable", async ({
  page,
  request,
}) => {
  const seedRes = await request.post("/api/dev/seed");
  expect(seedRes.ok()).toBeTruthy();
  const { project_id: projectId } = await seedRes.json();
  expect(projectId).toBeTruthy();

  await page.goto(`/projects/${projectId}/report`);

  // Business tab has the seeded green claim with its citation.
  await page.getByRole("button", { name: "Business", exact: true }).click();

  const claimItem = page.getByText(
    "North American revenue increased 18% in FY2025."
  );
  await expect(claimItem).toBeVisible();

  await page.getByRole("button", { name: "Source", exact: true }).click();

  // Source viewer opens and highlights the verbatim quote inside the
  // passage with a <mark> element.
  await expect(
    page.getByRole("heading", { name: "Source", exact: true })
  ).toBeVisible();
  await expect(page.locator("mark", { hasText: VERBATIM_QUOTE })).toBeVisible();

  // Financials tab: revenue is fully seeded, gross_profit was never
  // seeded, so its row must render "unavailable" cells rather than 0s or
  // blanks.
  await page.getByRole("button", { name: "Financials", exact: true }).click();

  const grossProfitRow = page.getByRole("row", { name: /Gross profit/ });
  await expect(grossProfitRow).toBeVisible();
  await expect(grossProfitRow.getByText("unavailable").first()).toBeVisible();
});
