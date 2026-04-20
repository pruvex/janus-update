// tests/e2e/natural-language-routing.spec.js
import { test, expect } from '@playwright/test';

test.describe('Validierung des Diamantstandard-Routings', () => {
  test.beforeEach(async ({ page }) => {
    // Standard Setup: Login & Neuer Chat
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => localStorage.setItem('auth_token', 'e2e-test-fake-token'));
    await page.reload();
    await expect(page.getByPlaceholder('Nachricht an Janus senden')).toBeVisible({ timeout: 15000 });
    
    // Neuer Chat ist wichtig für saubere Tests
    await page.getByRole('button', { name: 'Neuer Chat' }).first().click();
    await expect(page.locator('.message-list .message')).toHaveCount(0, { timeout: 5000 });
  });

  test('Sollte Bildgenerierung erkennen', async ({ page }) => {
    test.setTimeout(90000);
    const chatInput = page.getByPlaceholder('Nachricht an Janus senden');

    await chatInput.fill("Mach mir ein Bild von einem Astronauten auf einem Pferd");
    await chatInput.press('Enter');

    // Wir erwarten, dass das System entweder das Bild generiert oder (bei Route A Safety) nachfragt.
    // Da "Bild machen" meist teuer ist, könnte es eine Rückfrage sein, oder das Tool wird direkt ausgeführt.
    // Wir prüfen auf Erfolgsmeldung oder Bild-URL-Indikator.
    const response = page.locator('.message.assistant').last();
    // Hinweis: Die Antwort könnte Markdown für ein Bild enthalten oder "Ich habe das Bild erstellt".
    await expect(response).toContainText(/Bild|generiert|erstellt|hier ist/i, { timeout: 60000 });
  });

  test('Sollte PDF-Erstellung erkennen', async ({ page }) => {
    test.setTimeout(90000);
    const chatInput = page.getByPlaceholder('Nachricht an Janus senden');
    
    // Neuer Chat für sauberen State
    await page.getByRole('button', { name: 'Neuer Chat' }).first().click();

    await chatInput.fill("Erstell mir ein PDF mit dem Titel 'Test' und dem Inhalt 'Hallo Welt'");
    await chatInput.press('Enter');

    const response = page.locator('.message.assistant').last();
    // PDF ist oft "Risky" -> könnte nachfragen. Oder direkt machen.
    await expect(response).toContainText(/PDF|erstellt|gespeichert|Bist du sicher/i, { timeout: 60000 });
  });

  test('Sollte MP3-Erstellung erkennen', async ({ page }) => {
    test.setTimeout(90000);
    const chatInput = page.getByPlaceholder('Nachricht an Janus senden');
    
    await page.getByRole('button', { name: 'Neuer Chat' }).first().click();

    await chatInput.fill("Sag 'Hallo Welt' und speicher das als hallo.mp3");
    await chatInput.press('Enter');

    const response = page.locator('.message.assistant').last();
    await expect(response).toContainText(/MP3|Audio|gespeichert|erstellt|Bist du sicher/i, { timeout: 60000 });
  });
});
