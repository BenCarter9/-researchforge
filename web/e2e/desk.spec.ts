import { expect, test } from "@playwright/test";

test("desk page shows sourced TAKE/PASS calls, GLM-5.2 model id, and precomputed draft", async ({
  page,
}) => {
  await page.goto("/desk");

  await expect(page.getByRole("heading", { name: "Desk", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Rogo" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Fiscal.ai (formerly FinChat)" })
  ).toBeVisible();
  await expect(page.getByText("zai-org/GLM-5.2").first()).toBeVisible();
  await expect(page.getByText(/cached GLM-5.2 draft/i).first()).toBeVisible();
  await expect(page.getByText(/Loading desk/i)).toHaveCount(0);
  await expect(page.getByText(/\$160 million/i).first()).toBeVisible();
  await expect(page.getByText(/350,000 registered users/i).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Source" }).first()).toBeVisible();

  await page.getByRole("button", { name: /confirm take/i }).click();
  await expect(page.getByText(/confirmed by you/i)).toBeVisible();

  await page.getByText("Exact prompt and model id", { exact: true }).click();
  await expect(page.getByText("zai-org/GLM-5.2").nth(1)).toBeVisible();
});
