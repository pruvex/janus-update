// tests/e2e/diamant-routing.spec.js

import { test, expect } from '@playwright/test';

test.describe('Diamantstandard E2E-Szenario', () => {
  
  test.beforeEach(async ({ page }) => {
    // 1. Gehe zur Seite und injiziere den Login-Token
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'e2e-test-fake-token');
    });
    await page.reload();
    
    // 2. Warte auf die UI
    await expect(page.getByPlaceholder('Nachricht an Janus senden')).toBeVisible({ timeout: 15000 });
    
    // 3. Starte IMMER einen neuen Chat für einen sauberen Zustand
    await page.getByRole('button', { name: 'Neuer Chat' }).first().click();

    // 4. Warte, bis der Chat leer ist (keine alten Nachrichten)
    await expect(page.locator('.message-list .message')).toHaveCount(0, { timeout: 5000 });
  });
  
  test('Planner, Bestätigung und Safety Guardrail', async ({ page }) => {
    // Erhöhe das Timeout für den gesamten Test auf 90 Sekunden
    test.setTimeout(90000); 

    const chatInput = page.getByPlaceholder('Nachricht an Janus senden');

    // --- Schritt 1: Route B (Planner) auslösen ---
    await chatInput.fill("Ich muss nächste Woche zum Arzt.");
    await page.keyboard.press('Enter');
    
    // ASSERT 1 (ROBUST): Prüfe, ob die Antwort des Planners relevante Schlüsselwörter enthält.
    const plannerResponse = page.locator('.message.assistant').last();
    await expect(plannerResponse).toContainText(/details|uhrzeit|welcher tag|arzt/i, { timeout: 30000 });

    // --- Schritt 2: Den Plan bestätigen (Stateful Follow-Up) ---
    // Wir geben eine realistischere Antwort, die auch schon Daten enthält
    await chatInput.fill("Ja, Montag 9 Uhr bei Dr. Schmidt.");
    await page.keyboard.press('Enter');

    // ASSERT 2: Warte auf die Bestätigung der Ausführung
    const executionResponse = page.locator('.message.assistant').last();
    await expect(executionResponse).toContainText(/Termin erstellt|erledigt|gespeichert|eingetragen/i, { timeout: 30000 });

    // --- Schritt 3: Route A (Safety Guardrail) auslösen ---
    await chatInput.fill("Lösche meine Einkaufsliste.");
    await page.keyboard.press('Enter');
    
    // ASSERT 3: Warte auf die Sicherheits-Rückfrage
    const safetyResponse = page.locator('.message.assistant').last();
    await expect(safetyResponse).toContainText(/Bist du sicher|Bestätige/i, { timeout: 30000 });
  });
});
