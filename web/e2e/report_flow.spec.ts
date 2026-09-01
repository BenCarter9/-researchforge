import { expect, test } from "@playwright/test";

const BUSINESS_CLAIM =
  "Google Services generates revenue primarily from performance and brand advertising on Search, YouTube, and Network properties.";
const VERBATIM_QUOTE =
  "Google Services generates revenues primarily by delivering both performance and brand advertising that appears on Google Search & other properties, YouTube, and Google Network partners' properties";

test("demo path: home opens seeded GOOGL report, claim click shows quote, financials unavailable", async ({
  page,
  request,
}) => {
  const seedRes = await request.post("/api/dev/seed");
  expect(seedRes.ok()).toBeTruthy();
  const { project_id: projectId } = await seedRes.json();
  expect(projectId).toBe("e2e-project");

  await page.goto("/");
  await page.getByRole("link", { name: /open googl report/i }).click();
  await expect(page.getByRole("heading", { name: "GOOGL" })).toBeVisible();

  await page.getByRole("button", { name: "Business", exact: true }).click();
  await page.getByRole("button", { name: BUSINESS_CLAIM }).click();

  await expect(
    page.getByRole("heading", { name: "Source", exact: true })
  ).toBeVisible();
  await expect(page.locator("mark", { hasText: VERBATIM_QUOTE })).toBeVisible();

  await page.getByRole("button", { name: "Financials", exact: true }).click();
  const grossProfitRow = page.getByRole("row", { name: /Gross profit/ });
  await expect(grossProfitRow).toBeVisible();
  await expect(grossProfitRow.getByText("unavailable").first()).toBeVisible();
  await page.getByRole("button", { name: /^\+/ }).first().click();
  await expect(page.getByRole("heading", { name: "Formula" })).toBeVisible();
  await expect(page.getByText("(curr - prev) / prev")).toBeVisible();

  await page.getByRole("link", { name: /open the desk/i }).click();
  await expect(page.getByRole("heading", { name: "Desk", exact: true })).toBeVisible();
  await expect(page.getByText(/cached GLM-5.2 draft/i).first()).toBeVisible();
});
