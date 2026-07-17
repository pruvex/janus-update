// tests/functional/chat-core.spec.js
import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

function readInternalApiKey() {
  try {
    const cfgPath = path.join(os.homedir(), 'AppData', 'Roaming', 'Janus Projekt', 'config.json');
    const raw = fs.readFileSync(cfgPath, 'utf8');
    const cfg = JSON.parse(raw);
    return typeof cfg.api_key === 'string' ? cfg.api_key : '';
  } catch (_) {
    return '';
  }
}

test.describe('Kern-Funktionalität des Chats', () => {

  test('sollte einen neuen Chat starten und eine Antwort vom Modell erhalten', async ({ page }) => {
    test.setTimeout(60000);
    const internalApiKey = readInternalApiKey();

    // Avoid privacy modal interference in automation.
    await page.addInitScript(() => {
      try {
        localStorage.setItem(
          'janus_beta_privacy_ack_v1',
          JSON.stringify({
            accepted: true,
            noticeVersion: '2026-07-17.1',
            acceptedAt: new Date().toISOString(),
          })
        );
      } catch (_) {
        // best effort
      }
    });
    await page.addInitScript((apiKey) => {
      // Emulate minimal Electron preload bridge in browser-based Playwright runs.
      window.electron = {
        getApiKey: async () => apiKey,
      };
    }, internalApiKey);

    await page.route('**/api/models/catalog', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'gpt-5.4-mini',
            name: 'GPT-5.4 mini',
            provider: 'openai',
            type: 'text',
          },
        ]),
      });
    });
    await page.route('**/api/models/selection/openai', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ selected_models: ['gpt-5.4-mini'] }),
      });
    });
    await page.route('**/api/local-llm/models', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ models: [] }),
      });
    });
    await page.route('**/api/last-used-model', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ provider: 'openai', model: 'gpt-5.4-mini' }),
      });
    });
    await page.route('**/api/chat/stream', async (route) => {
      const request = route.request().postDataJSON();
      expect(request.provider).toBe('openai');
      expect(request.model).toBe('gpt-5.4-mini');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: [
          'data: {"type":"text","content":"Hallo aus dem deterministischen Chat-Core-Test.","partial":false}',
          '',
          'data: {"type":"done"}',
          '',
          '',
        ].join('\n'),
      });
    });

    // 1. Starten
    await page.goto('/');

    // 2. Neuer Chat
    const newChatButton = page.getByRole('button', { name: /neuer chat/i });
    await expect(newChatButton).toBeVisible({ timeout: 15000 });
    await newChatButton.click();

    // The chat shell becomes visible before the asynchronous catalog/selection
    // bootstrap is necessarily stable. Wait for the repeatable effective
    // provider/model state before submitting, otherwise the request can race
    // with an empty model value.
    await expect(page.locator('#provider-select')).toHaveValue('openai', { timeout: 15000 });
    await expect(page.locator('#model-select')).toHaveValue('gpt-5.4-mini', { timeout: 15000 });
    await expect(page.locator('#chat-header-model-A')).toHaveValue('gpt-5.4-mini', { timeout: 15000 });

    // 3. Nachricht tippen
    const chatWindowA = page.getByRole('region', { name: /chat-fenster a/i });
    const messageInput = page.locator('#user-input-A');
    await expect(messageInput).toBeVisible(); 
    
    const myMessage = 'Hallo Janus';
    await messageInput.fill(myMessage);

    // Warten bis der Senden-Button klickbar ist, statt einer festen Zeit
    const sendButton = chatWindowA.getByRole('button', { name: /senden/i });
    await expect(sendButton).toBeEnabled();
    
    const streamResponsePromise = page.waitForResponse(
      (res) => res.url().includes('/api/chat/stream') && res.request().method() === 'POST',
      { timeout: 15000 }
    );

    await page.evaluate(() => {
      const form = document.getElementById('chat-form-A');
      if (form) {
        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
      }
    });

    const streamResponse = await streamResponsePromise;
    expect(streamResponse.status()).toBe(200);

    // 4. Prüfen ob Antwort kommt
    const assistantResponse = chatWindowA.locator('.message.assistant .bubble').last();
    await expect(assistantResponse).toBeVisible({ timeout: 30000 });
    await expect(assistantResponse).not.toBeEmpty();
  });
});
