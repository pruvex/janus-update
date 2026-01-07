import { test } from '@playwright/test';

test('Spionage-Test: HTML Struktur auslesen', async ({ page }) => {
  // 1. App laden
  await page.goto('/');
  
  // 2. Chat starten und "hi" senden (dein Code)
  await page.getByRole('button', { name: /neuer chat/i }).click();
  const input = page.getByRole('textbox', { name: 'Nachricht an Janus senden...' });
  await input.click();
  await input.fill('hi');
  await input.press('Enter');
  
  // 3. Kurz warten, bis die Antwort da ist (5 Sekunden)
  await page.waitForTimeout(5000);
  
  // 4. Den HTML-Code des Chat-Bereichs in die Konsole schreiben
  // Wir suchen im 'chat-view', da wir wissen, dass dieser existiert.
  const htmlContent = await page.locator('#chat-view').innerHTML();
  
  console.log("---------------------------------------------------");
  console.log("--- HIER IST DER HTML CODE DER CHAT ANSICHT ---");
  console.log(htmlContent);
  console.log("---------------------------------------------------");
});
