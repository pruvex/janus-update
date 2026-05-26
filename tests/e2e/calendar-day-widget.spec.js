import { expect, test } from "@playwright/test";

test.describe("Tages-Panel (Diamond rail)", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/calendar/events**", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ events: [], conflicts: [] }),
      });
    });
  });

  test("Kennzahlen, + Termin-Overlay, × schließt Rail", async ({ page }) => {
    await page.goto("http://localhost:5173/");
    await page.evaluate(() => {
      localStorage.setItem("auth_token", "e2e-test-fake-token");
      localStorage.setItem("janus_calendar_day_widget_visible", "1");
    });
    await page.reload();

    await expect(page.getByPlaceholder("Nachricht an Janus senden...").first()).toBeVisible({
      timeout: 15000,
    });

    const rail = page.locator("#calendar-day-widget-rail");
    await expect(rail).not.toHaveAttribute("hidden");
    await expect(rail.getByText("Termine").first()).toBeVisible();

    await page.locator("#cdw-quick-create").click();
    await expect(page.locator("#calendar-create-dialog-overlay")).toBeVisible();
    await page.locator('#calendar-create-dialog-overlay button[data-close="cancel"]').click();
    await expect(page.locator("#calendar-create-dialog-overlay")).toHaveCount(0);

    await expect(rail).not.toHaveAttribute("hidden");
    await page.getByRole("button", { name: "Tages-Panel ausblenden" }).click();
    await expect(rail).toHaveAttribute("hidden");
  });

  test("Escape schließt Rail ohne Dock-Modul", async ({ page }) => {
    await page.goto("http://localhost:5173/");
    await page.evaluate(() => {
      localStorage.setItem("auth_token", "e2e-test-fake-token");
      localStorage.setItem("janus_calendar_day_widget_visible", "1");
    });
    await page.reload();

    await expect(page.getByPlaceholder("Nachricht an Janus senden...").first()).toBeVisible({
      timeout: 15000,
    });

    const rail = page.locator("#calendar-day-widget-rail");
    await expect(rail).not.toHaveAttribute("hidden");
    await page.keyboard.press("Escape");
    await expect(rail).toHaveAttribute("hidden");
  });
});
