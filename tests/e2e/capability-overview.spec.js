// tests/e2e/capability-overview.spec.js

import { test, expect } from '@playwright/test';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

function base64Url(input) {
  return Buffer.from(input)
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
}

function loadJanusAppDataConfig() {
  const appData = process.env.APPDATA || '';
  const configPath = path.join(appData, 'Janus Projekt', 'config.json');
  return { configPath, config: JSON.parse(fs.readFileSync(configPath, 'utf-8')) };
}

function createE2eJwt() {
  const { configPath, config } = loadJanusAppDataConfig();
  const secret = config.jwt_secret_key;
  if (!secret) throw new Error(`jwt_secret_key missing in ${configPath}`);

  const header = { alg: 'HS256', typ: 'JWT' };
  const payload = {
    sub: 'local_user',
    scopes: ['me', 'settings:write'],
    exp: Math.floor(Date.now() / 1000) + 60 * 60,
  };
  const unsigned = `${base64Url(JSON.stringify(header))}.${base64Url(JSON.stringify(payload))}`;
  const signature = crypto
    .createHmac('sha256', secret)
    .update(unsigned)
    .digest('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
  return `${unsigned}.${signature}`;
}

/** Browser hat kein Electron → app.js fügt keinen X-Janus-Internal-Key ein; Backend verlangt ihn für /api/*. */
async function installInternalApiKeyRoute(page, internalKey) {
  if (!internalKey) {
    throw new Error('api_key missing in Janus config.json (required for E2E against real backend)');
  }
  const handler = async (route) => {
    const headers = { ...route.request().headers() };
    headers['X-Janus-Internal-Key'] = internalKey;
    await route.continue({ headers });
  };
  await page.route('http://127.0.0.1:8001/api/**', handler);
  await page.route('http://localhost:8001/api/**', handler);
}

/** Gleicher Sendepfad wie Form-Submit; dock-bar blockiert echte Klicks auf „Senden“. */
async function sendChatMessageWindowA(page) {
  await page.evaluate(async () => {
    const { sendMessage } = await import('/js/chat.js');
    await sendMessage('A');
  });
}

test.describe('Capability Overview E2E Tests (TASK-069)', () => {
  // Gemeinsame sqlite e2e DB + Backend: parallele Worker führen zu Timeouts bei sendMessage/stream
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ page }) => {
    const { config } = loadJanusAppDataConfig();
    await installInternalApiKeyRoute(page, config.api_key);

    // 1. Gehe zur Seite und injiziere den Login-Token
    await page.goto('http://localhost:5173/');
    const token = createE2eJwt();
    await page.evaluate(() => {
      localStorage.clear();
    });
    await page.evaluate((jwt) => {
      localStorage.setItem('auth_token', jwt);
    }, token);
    await page.reload();
    await page.waitForFunction(async () => {
      const jwt = localStorage.getItem('auth_token');
      if (!jwt) return false;
      const response = await fetch('http://127.0.0.1:8001/api/users/me', {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      return response.ok;
    }, null, { timeout: 15000 });

    // 2. Warte, bis die App stabil geladen ist (Neuer Chat Button sichtbar)
    await expect(page.getByRole('button', { name: 'Neuer Chat' })).toBeVisible({ timeout: 15000 });

    // 3. Scoping auf Fenster A, um Eindeutigkeit im Split-View sicherzustellen
    const chatInput = page.getByRole('region', { name: 'Chat-Fenster A' })
                      .getByPlaceholder(/Nachricht an Janus senden/);
    await expect(chatInput).toBeVisible({ timeout: 15000 });

    // 4. Fenster A aktivieren (createNewChat nutzt getActiveWindowId)
    await page.getByRole('region', { name: 'Chat-Fenster A' }).click();

    // 5. Neuer Chat — auf erfolgreiches POST warten (leere Message-Liste allein reicht nicht)
    const chatsPost = page.waitForResponse(
      (res) =>
        res.request().method() === 'POST' &&
        /\/api\/chats\/?(\?|$)/.test(new URL(res.url()).pathname) &&
        res.ok(),
      { timeout: 20000 },
    );
    await page.getByRole('button', { name: 'Neuer Chat' }).first().click();
    await chatsPost;

    // 6. Fenster A: leerer Verlauf
    await expect(page.locator('#chat-messages-A .message')).toHaveCount(0, { timeout: 5000 });
  });

  test('Capability Overview: Fast-Path für "Was kannst du?"', async ({ page }) => {
    // Scoping auf Fenster A, um Eindeutigkeit im Split-View sicherzustellen
    const chatInput = page.getByRole('region', { name: 'Chat-Fenster A' })
                      .getByPlaceholder(/Nachricht an Janus senden/);

    // 1. Trigger-Phrase eingeben
    await chatInput.fill("Was kannst du?");
    await sendChatMessageWindowA(page);

    // 2. Warte auf die Antwort (Fast-Path sollte schnell sein, Timeout auf 10000ms erhöht)
    const assistantResponse = page.locator('#chat-messages-A .message.assistant').last();
    await expect(assistantResponse).toBeVisible({ timeout: 20000 });

    // 3. Assertion: Header muss nach Markdown-Rendering sichtbar sein
    await expect(assistantResponse).toContainText('Das kann ich aktuell');

    // 4. Assertion: Mindestens eine Kategorieüberschrift muss sichtbar sein
    await expect(assistantResponse).toContainText(/Kalender & Termine|Sonstiges|Updates & Installation/);

    // 5. Assertion: Mindestens eine Capability muss angezeigt werden
    await expect(assistantResponse).toContainText(/Termine abrufen|Termin erstellen|Janus aktualisieren/);

    // 6. Assertion: Keine technischen Interna im UI
    const responseText = await assistantResponse.textContent();
    expect(responseText).not.toMatch(/backend\/|frontend\/|IPC|task_|\.py|\.js/i);
  });

  test('Capability Overview: Kalender-Kategorie sichtbar', async ({ page }) => {
    // Scoping auf Fenster A, um Eindeutigkeit im Split-View sicherzustellen
    const chatInput = page.getByRole('region', { name: 'Chat-Fenster A' })
                      .getByPlaceholder(/Nachricht an Janus senden/);

    await chatInput.fill("Was kannst du?");
    await sendChatMessageWindowA(page);

    const assistantResponse = page.locator('#chat-messages-A .message.assistant').last();
    await expect(assistantResponse).toBeVisible({ timeout: 20000 });

    // Spezifische Assertion: Kalender-Kategorie sollte sichtbar sein
    await expect(assistantResponse).toContainText(/Kalender|Termine/i);

    // Spezifische Capability sollte sichtbar sein
    await expect(assistantResponse).toContainText(/Termine abrufen|Termin erstellen/i);
  });
});
