import { test, expect } from '@playwright/test';

test('DEBUG REPRODUCTION: TC-001 Weather inference - Capture console error', async ({ page }) => {
  const consoleErrors = [];
  
  // Capture all console errors with full details
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push({
        text: msg.text(),
        location: msg.location(),
        stack: msg.stack ? msg.stack().toString() : 'no stack'
      });
      console.log('CONSOLE ERROR CAPTURED:', {
        text: msg.text(),
        location: msg.location(),
        stack: msg.stack ? msg.stack().toString() : 'no stack'
      });
    }
  });

  // Navigate to Janus
  await page.goto('http://localhost:5173/');
  await page.waitForLoadState('networkidle');
  
  // Wait for chat windows to be visible
  await page.waitForSelector('#chat-window-A', { timeout: 10000 });
  
  // Click on chat window A to focus
  await page.click('#chat-window-A');
  
  // Type the prompt
  const chatInput = page.locator('#chat-input-A');
  await chatInput.fill('Brauche ich morgen in München einen Regenschirm?');
  
  // Click send button
  await page.click('#send-button-A');
  
  // Wait for assistant bubble to appear (with timeout)
  try {
    await page.waitForSelector('#chat-messages-A .assistant-message', { timeout: 30000 });
  } catch (e) {
    console.log('Assistant bubble did not appear within timeout');
  }
  
  // Wait a bit more for any delayed errors
  await page.waitForTimeout(5000);
  
  // Report findings
  console.log('=== REPRODUCTION REPORT ===');
  console.log('Total console errors captured:', consoleErrors.length);
  consoleErrors.forEach((err, index) => {
    console.log(`Error ${index + 1}:`);
    console.log('  Text:', err.text);
    console.log('  Location:', err.location);
    console.log('  Stack:', err.stack);
  });
  
  // Check if "win is not defined" error occurred
  const winError = consoleErrors.find(err => err.text.includes('win is not defined'));
  if (winError) {
    console.log('=== CRITICAL FINDING ===');
    console.log('Found "win is not defined" error!');
    console.log('Location:', winError.location);
    console.log('Stack:', winError.stack);
  }
  
  // This test always passes - it's for information gathering only
  expect(consoleErrors.length).toBeGreaterThanOrEqual(0);
});
