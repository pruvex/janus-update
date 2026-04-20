// tests/functional/chat-core.spec.js
import { test, expect } from '@playwright/test';

test.describe('Kern-Funktionalität des Chats', () => {

  test('sollte einen neuen Chat starten und eine Antwort vom Modell erhalten', async ({ page }) => {
    test.setTimeout(60000);

    // 1. Starten
    await page.goto('/');

    // 2. Neuer Chat
    const newChatButton = page.getByRole('button', { name: /neuer chat/i });
    await expect(newChatButton).toBeVisible({ timeout: 15000 });
    await newChatButton.click();

    // 3. Nachricht tippen
    const messageInput = page.getByRole('textbox', { name: 'Nachricht an Janus senden...' });
    await expect(messageInput).toBeVisible(); 
    
    const myMessage = 'Hallo Janus';
    await messageInput.fill(myMessage);

    // Warten bis der Senden-Button klickbar ist, statt einer festen Zeit
    const sendButton = page.getByRole('button', { name: /senden/i });
    await expect(sendButton).toBeEnabled();
    
    await messageInput.press('Enter');

    // 4. Prüfen ob Input leer
    await expect(messageInput).toBeEmpty();

    // 5. Prüfen ob eigene Nachricht da ist
    const userMessage = page.locator('.message.user').filter({ hasText: myMessage }).last();
    await expect(userMessage).toBeVisible({ timeout: 10000 });

    // 6. Prüfen ob Antwort kommt
    const assistantResponse = page.locator('.message.assistant').last();
    await expect(assistantResponse).toBeVisible({ timeout: 30000 });
    await expect(assistantResponse).not.toBeEmpty();
  });
});