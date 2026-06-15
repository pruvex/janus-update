import { test, expect } from "@playwright/test";

test("broken generated runner fixture", async ({ page }) => {
  await page.goto("https://example.invalid")
  await expect(page).toHaveURL(/example/)
