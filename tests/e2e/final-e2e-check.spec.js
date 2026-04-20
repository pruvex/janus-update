// tests/e2e/final-e2e-check.spec.js

import { test, expect } from '@playwright/test';

test.describe('Finaler End-to-End Check', () => {

  test('Sollte eine einfache Konversation führen und die Diamant-Logik zeigen', async ({ page }) => {
    // Maximales Timeout für den gesamten Test
    test.setTimeout(120000); // 2 Minuten

    // 1. Starten und Login simulieren
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'e2e-test-fake-token');
    });
    await page.reload();

    // 2. Warten auf UI und neuen Chat starten
    const newChatButton = page.getByRole('button', { name: /neuer chat/i }).first();
    await expect(newChatButton).toBeVisible({ timeout: 20000 });
    await newChatButton.click();

    const chatInput = page.getByRole('textbox', { name: 'Nachricht an Janus senden...' });
    await expect(chatInput).toBeVisible(); 
    
    // --- SCHRITT 1: EINE EINFACHE FRAGE ---
    await chatInput.fill("Hallo Janus");
    await chatInput.press('Enter');

    // ASSERT 1: Warte bis zu 45 Sekunden auf eine Begrüßungsantwort.
    await expect(page.locator('.message.assistant').last()).toContainText(/Hallo|Schön dich zu hören|Womit kann ich/i, { timeout: 45000 });

    // --- SCHRITT 2: PLANNER (ROUTE B) AUSLÖSEN ---
    await chatInput.fill("Ich muss nächste Woche zum Arzt.");
    await chatInput.press('Enter');
    
    // ASSERT 2: Warte bis zu 45 Sekunden auf die Rückfrage des Planners.
    await expect(page.locator('.message.assistant').last()).toContainText(/details|uhrzeit|welcher tag|arzt/i, { timeout: 45000 });
  });
});