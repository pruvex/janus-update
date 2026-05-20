import { test, expect } from '@playwright/test';

test.describe('BACKLOG-023 Timeout Fix Verification', () => {
  test.setTimeout(60000);

  async function runPromptInChatWindow(page, prompt) {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    
    // Type prompt in Chat Window A
    const textarea = page.locator('#user-input-A');
    await textarea.fill(prompt);
    
    // Send message
    const sendButton = page.getByRole('button', { name: 'Senden' }).first();
    await sendButton.click();
    
    // Wait for response (max 30s)
    await page.waitForSelector('.message.assistant', { timeout: 30000 });
    
    // Get response text
    const responseElement = page.locator('.message.assistant').last();
    const responseText = await responseElement.textContent();
    
    return { responseText: responseText || '' };
  }

  test('TC-001: Sequential Request 1 - Weather', async ({ page }) => {
    const prompt = 'Wie ist das Wetter heute?';
    const { responseText } = await runPromptInChatWindow(page, prompt);
    
    console.log('TC-001 Response:', responseText.substring(0, 200));
    
    const hasWeatherTerms = ['Wetter', 'Grad', 'Temperatur'].some((term) => 
      responseText.toLowerCase().includes(term.toLowerCase())
    );
    const hasNoErrors = !['timeout', 'Fehler', 'keine Antwort'].some((term) => 
      responseText.toLowerCase().includes(term.toLowerCase())
    );
    
    expect(hasWeatherTerms && hasNoErrors, `TC-001 failed: Expected weather terms, got: ${responseText.substring(0, 200)}`).toBe(true);
  });

  test('TC-002: Sequential Request 2 - Weather (no timeout)', async ({ page }) => {
    const prompt = 'Wie ist das Wetter morgen?';
    const { responseText } = await runPromptInChatWindow(page, prompt);
    
    console.log('TC-002 Response:', responseText.substring(0, 200));
    
    const hasWeatherTerms = ['Wetter', 'Grad', 'Temperatur'].some((term) => 
      responseText.toLowerCase().includes(term.toLowerCase())
    );
    const hasNoErrors = !['timeout', 'Fehler', 'keine Antwort'].some((term) => 
      responseText.toLowerCase().includes(term.toLowerCase())
    );
    
    expect(hasWeatherTerms && hasNoErrors, `TC-002 failed: Expected weather terms without timeout, got: ${responseText.substring(0, 200)}`).toBe(true);
  });
});
