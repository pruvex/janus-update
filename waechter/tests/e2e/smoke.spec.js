import { test, expect } from '@playwright/test';

test('Smoke Test: App startet und rendert Hauptkomponenten', async ({ page }) => {
  // Navigiere zur Anwendung (baseURL ist in playwright.config.js konfiguriert)
  await page.goto('/');

  // 1. Überprüfe, ob die Sidebar sichtbar ist
  await expect(page.locator('#sidebar')).toBeVisible();

  // 2. Überprüfe, ob das "Einstellungen"-Button in der Sidebar sichtbar ist
  await expect(page.locator('#settings-btn')).toBeVisible();

  // 3. Überprüfe, ob das Chat-Fenster (oder sein Container) im DOM vorhanden ist
  // Wir prüfen hier nur auf 'count > 0', da es beweglich ist und nicht immer "sichtbar" sein muss
  await expect(page.locator('#chat-view')).toHaveCount(1);
    
  // 4. Überprüfe, ob das Chat-Eingabefeld vorhanden ist
  await expect(page.locator('#chat-input')).toBeVisible();
});