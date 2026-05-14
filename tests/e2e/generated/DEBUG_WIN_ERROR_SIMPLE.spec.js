import { test, expect } from '@playwright/test';

test('DEBUG SIMPLE: Capture console error for win is not defined', async ({ page }) => {
  const consoleErrors = [];
  
  // Capture all console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push({
        text: msg.text(),
        location: msg.location()
      });
      console.log('CONSOLE ERROR:', msg.text(), 'at', msg.location());
    }
  });

  // Navigate to Janus
  await page.goto('http://localhost:5173/');
  await page.waitForLoadState('domcontentloaded');
  
  // Wait for chat window
  await page.waitForSelector('#chat-window-A', { timeout: 10000 });
  
  // Type prompt
  await page.fill('#chat-input-A', 'Brauche ich morgen in München einen Regenschirm?');
  
  // Click send
  await page.click('#send-button-A');
  
  // Wait 10 seconds for any errors
  await page.waitForTimeout(10000);
  
  // Report
  console.log('=== CONSOLE ERRORS ===');
  console.log('Total:', consoleErrors.length);
  consoleErrors.forEach(err => console.log('-', err.text, 'at', err.location));
  
  const winError = consoleErrors.find(err => err.text.includes('win is not defined'));
  if (winError) {
    console.log('=== FOUND WIN ERROR ===');
    console.log('Location:', winError.location);
  }
  
  expect(consoleErrors.length).toBeGreaterThanOrEqual(0);
});
