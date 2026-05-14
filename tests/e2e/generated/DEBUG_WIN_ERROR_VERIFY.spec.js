import { test, expect } from '@playwright/test';

test('DEBUG VERIFY: Check for win is not defined error on page load', async ({ page }) => {
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
  
  // Wait for page to fully load
  await page.waitForTimeout(5000);
  
  // Report
  console.log('=== CONSOLE ERRORS ===');
  console.log('Total:', consoleErrors.length);
  consoleErrors.forEach((err, index) => {
    console.log(`Error ${index + 1}:`);
    console.log('  Text:', err.text);
    console.log('  Location:', JSON.stringify(err.location));
  });
  
  const winError = consoleErrors.find(err => err.text.includes('win is not defined'));
  if (winError) {
    console.log('=== FOUND WIN ERROR ===');
    console.log('Location:', JSON.stringify(winError.location));
    throw new Error('win is not defined error still present');
  } else {
    console.log('=== NO WIN ERROR FOUND ===');
  }
  
  // Only fail if win error is found, ignore other console errors for now
  if (winError) {
    throw new Error('win is not defined error still present');
  }
});
