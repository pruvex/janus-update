import { expect, test } from '@playwright/test';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';


const SENTINEL_A = 'TEST_OPENROUTER_SECRET_ALPHA';
const SENTINEL_B = 'TEST_OPENROUTER_SECRET_BETA';


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


async function installInternalApiKeyRoute(page, internalKey) {
  const handler = async (route) => {
    const headers = { ...route.request().headers(), 'X-Janus-Internal-Key': internalKey };
    await route.continue({ headers });
  };
  await page.route('http://127.0.0.1:8001/api/**', handler);
  await page.route('http://localhost:8001/api/**', handler);
}


async function acknowledgeBetaPrivacyNoticeIfVisible(page) {
  const modal = page.locator('#beta-privacy-modal');
  if (await modal.isVisible()) {
    await page.getByRole('checkbox', {
      name: /Ich habe verstanden, welche Daten Janus in der Beta verarbeitet/i,
    }).check();
    await page.getByRole('button', { name: 'Akzeptieren' }).click();
    await expect(modal).toBeHidden();
  }
}


async function openApiKeySettings(page) {
  await page.getByRole('button', { name: 'Einstellungen' }).click();
  await page.getByRole('link', { name: 'API Keys' }).click();
  await expect(page.locator('#api-key-section')).toBeVisible();
}


test.describe('OpenRouter credential settings (TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2)', () => {
  test.describe.configure({ mode: 'serial', timeout: 60_000 });

  let openrouterState;
  let storedOpenrouterKey;
  let nextValidationState;
  let simulateTechnicalValidationFailure;
  let saveDelayMs;
  let deleteRequests;
  let consoleMessages;

  test.beforeEach(async ({ page }) => {
    openrouterState = { present: false, masked: null, state: 'UNVERIFIED' };
    storedOpenrouterKey = null;
    nextValidationState = 'VALID';
    simulateTechnicalValidationFailure = false;
    saveDelayMs = 0;
    deleteRequests = 0;
    consoleMessages = [];
    page.on('console', (message) => consoleMessages.push(message.text()));

    const { config } = loadJanusAppDataConfig();
    await installInternalApiKeyRoute(page, config.api_key);

    await page.route('**/api/keys**', async (route) => {
      const request = route.request();
      const url = new URL(request.url());

      if (request.method() === 'GET' && url.pathname.endsWith('/api/keys')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            api_keys: {
              openai: '********',
              openrouter: openrouterState,
            },
          }),
        });
        return;
      }

      if (request.method() === 'POST' && url.pathname.endsWith('/api/keys')) {
        const payload = request.postDataJSON();
        expect(payload.provider).toBe('openrouter');
        expect([SENTINEL_A, SENTINEL_B]).toContain(payload.api_key);
        if (saveDelayMs) await new Promise((resolve) => setTimeout(resolve, saveDelayMs));
        const sameExactConfirmedKey =
          storedOpenrouterKey === payload.api_key && openrouterState.state === 'VALID';
        const renderedState = simulateTechnicalValidationFailure
          ? (sameExactConfirmedKey ? 'VALID' : 'UNVERIFIED')
          : nextValidationState;
        storedOpenrouterKey = payload.api_key;
        openrouterState = { present: true, masked: '********', state: renderedState };
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'OpenRouter API key saved.',
            provider: 'openrouter',
            key: openrouterState,
          }),
        });
        return;
      }

      if (request.method() === 'DELETE' && url.pathname.endsWith('/api/keys/openrouter')) {
        deleteRequests += 1;
        openrouterState = { present: false, masked: null, state: 'UNVERIFIED' };
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'OpenRouter API key deleted.',
            provider: 'openrouter',
            key: openrouterState,
          }),
        });
        return;
      }

      await route.abort();
    });

    await page.route('**/api/codex-connection', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          available: true,
          codex_connection: {
            connection_state: 'disconnected',
            account_identifier: null,
            workspace_id: null,
            workspace_display: null,
            auth_mode: null,
            plan_type: null,
            retry_reason: null,
            login_pending: false,
            login_id: null,
            capabilities: {
              managed_chatgpt_login: true,
              keyring_only: true,
              janus_isolated: true,
            },
          },
        }),
      });
    });

    await page.goto('http://localhost:5173/');
    const token = createE2eJwt();
    await page.evaluate(() => localStorage.clear());
    await page.evaluate((jwt) => localStorage.setItem('auth_token', jwt), token);
    const appReady = page.waitForEvent('console', {
      predicate: (message) => message.text().includes('Initialization complete. Janus is ready.'),
      timeout: 30_000,
    });
    await page.reload();
    await appReady;
    await acknowledgeBetaPrivacyNoticeIfVisible(page);
    await openApiKeySettings(page);
  });

  test('updates VALID, INVALID, and UNVERIFIED in place without exposing the key', async ({ page }) => {
    const status = page.locator('#openrouter-key-status');
    await expect(status).toContainText('OpenRouter: nicht gespeichert · UNVERIFIED');
    await expect(page.locator('#codex-connection-card')).toBeVisible();

    await page.locator('#provider-input').selectOption('openrouter');
    await page.locator('#api-key-input').fill(SENTINEL_A);
    saveDelayMs = 250;
    const saveClick = page.getByRole('button', { name: 'Speichern' }).click();
    await expect(page.getByRole('button', { name: 'Speichere...' })).toBeDisabled();
    await saveClick;
    await expect(status).toContainText('OpenRouter: gespeichert · VALID');
    await expect(page.locator('#api-key-section')).toBeVisible();

    nextValidationState = 'INVALID';
    saveDelayMs = 0;
    await page.locator('#api-key-input').fill(SENTINEL_B);
    await page.getByRole('button', { name: 'Speichern' }).click();
    await expect(status).toContainText('OpenRouter: gespeichert · INVALID');

    nextValidationState = 'UNVERIFIED';
    await page.locator('#api-key-input').fill(SENTINEL_B);
    await page.getByRole('button', { name: 'Speichern' }).click();
    await expect(status).toContainText('OpenRouter: gespeichert · UNVERIFIED');

    const bodyText = await page.locator('body').innerText();
    expect(bodyText).not.toContain(SENTINEL_A);
    expect(bodyText).not.toContain(SENTINEL_B);
    expect(consoleMessages.join('\n')).not.toContain(SENTINEL_A);
    expect(consoleMessages.join('\n')).not.toContain(SENTINEL_B);
    await expect(page.getByRole('button', { name: /Modelle für openrouter verwalten/i })).toHaveCount(0);
    await expect(page.locator('#codex-connection-card')).toBeVisible();
  });

  test('keeps the same exact previously VALID key VALID after a technical revalidation failure', async ({ page }) => {
    const status = page.locator('#openrouter-key-status');
    await page.locator('#provider-input').selectOption('openrouter');
    await page.locator('#api-key-input').fill(SENTINEL_A);
    await page.getByRole('button', { name: 'Speichern' }).click();
    await expect(status).toContainText('OpenRouter: gespeichert · VALID');

    simulateTechnicalValidationFailure = true;
    await page.locator('#api-key-input').fill(SENTINEL_A);
    await page.getByRole('button', { name: 'Speichern' }).click();

    await expect(status).toContainText('OpenRouter: gespeichert · VALID');
    await expect(page.locator('#openrouter-key-feedback')).toContainText(
      'OpenRouter-Key-Status wurde aktualisiert.'
    );
    expect(await page.locator('body').innerText()).not.toContain(SENTINEL_A);
    expect(consoleMessages.join('\n')).not.toContain(SENTINEL_A);
    await expect(page.locator('#codex-connection-card')).toBeVisible();
    await expect(page.getByRole('button', { name: /Modelle für openrouter verwalten/i })).toHaveCount(0);
  });

  test('deletes only OpenRouter state and leaves the ChatGPT card in place', async ({ page }) => {
    nextValidationState = 'VALID';
    await page.locator('#provider-input').selectOption('openrouter');
    await page.locator('#api-key-input').fill(SENTINEL_A);
    await page.getByRole('button', { name: 'Speichern' }).click();
    await expect(page.locator('#openrouter-key-status')).toContainText('gespeichert · VALID');

    await page.getByRole('button', { name: 'OpenRouter-Key löschen' }).click();

    await expect(page.locator('#openrouter-key-status')).toContainText(
      'OpenRouter: nicht gespeichert · UNVERIFIED'
    );
    expect(deleteRequests).toBe(1);
    await expect(page.locator('#codex-connection-card')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Mit ChatGPT anmelden' })).toBeVisible();
    await expect(page.locator('#api-key-section')).toBeVisible();
  });
});
