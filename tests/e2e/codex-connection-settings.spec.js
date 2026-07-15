import { expect, test } from '@playwright/test';
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

async function installInternalApiKeyRoute(page, internalKey) {
  const handler = async (route) => {
    const headers = { ...route.request().headers() };
    headers['X-Janus-Internal-Key'] = internalKey;
    await route.continue({ headers });
  };
  await page.route('http://127.0.0.1:8001/api/**', handler);
  await page.route('http://localhost:8001/api/**', handler);
}

const disconnectedState = {
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
};

const connectedState = {
  ...disconnectedState,
  connection_state: 'connected',
  account_identifier: 'user@example.com',
  workspace_display: 'Default Workspace',
  workspace_id: 'ws-1',
  auth_mode: 'chatgpt',
};

let codexState = { ...disconnectedState };
let verifiedChatgptModels = [];
let modelVerificationFailed = false;
let openedVerificationUrls = [];
let loginFailure = false;
let nextStatusState = null;
let replacementCompletionState = null;
let logoutRequests = 0;
let lastUsedModelState = { provider: 'openai', model: 'gpt-3.5-turbo' };

async function installCodexConnectionMocks(page) {
  await page.route('**/api/codex-connection**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const pathname = url.pathname;

    if (request.method() === 'GET' && pathname.endsWith('/api/codex-connection')) {
      if (nextStatusState) {
        codexState = nextStatusState;
        nextStatusState = null;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          codex_connection: codexState,
          available: true,
          model_availability: codexState.connection_state === 'connected'
            ? {
                state: modelVerificationFailed ? 'unavailable' : 'available',
                models: modelVerificationFailed ? [] : verifiedChatgptModels,
              }
            : undefined,
        }),
      });
      return;
    }

    if (request.method() === 'POST' && pathname.endsWith('/api/codex-connection/login')) {
      if (loginFailure) {
        await route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: { code: 'codex_connection_unavailable', codex_connection: codexState },
          }),
        });
        return;
      }
      codexState = {
        ...codexState,
        connection_state: 'connecting',
        login_pending: true,
        login_id: 'login-e2e-1',
      };
      if (replacementCompletionState) {
        nextStatusState = replacementCompletionState;
        replacementCompletionState = null;
      }
      const verificationUrl = request.headers()['x-test-auth-scheme'] === 'http'
        ? 'http://evil.example/login'
        : 'https://auth.openai.com/codex/device';
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          verification_url: verificationUrl,
          user_code: 'E2E-CODE',
          login_id: 'login-e2e-1',
          codex_connection: codexState,
        }),
      });
      return;
    }

    if (request.method() === 'POST' && pathname.endsWith('/api/codex-connection/login/cancel')) {
      codexState = codexState.account_identifier
        ? { ...connectedState }
        : { ...disconnectedState };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ codex_connection: codexState }),
      });
      return;
    }

    if (request.method() === 'POST' && pathname.endsWith('/api/codex-connection/logout')) {
      logoutRequests += 1;
      codexState = { ...disconnectedState };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ codex_connection: codexState }),
      });
      return;
    }

    if (request.method() === 'POST' && pathname.endsWith('/api/codex-connection/retry')) {
      codexState = { ...disconnectedState };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ codex_connection: codexState }),
      });
      return;
    }

    await route.continue();
  });

  await page.route('http://127.0.0.1:8001/api/models/catalog', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(modelVerificationFailed ? [] : verifiedChatgptModels),
    });
  });

  await page.route('http://127.0.0.1:8001/api/local-llm/models', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ models: [] }),
    });
  });

  await page.route('http://127.0.0.1:8001/api/last-used-model', async (route) => {
    const request = route.request();

    if (request.method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(lastUsedModelState),
      });
      return;
    }

    if (request.method() === 'PUT') {
      const payload = request.postDataJSON();
      lastUsedModelState = { provider: payload.provider, model: payload.model };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({}),
      });
      return;
    }

    await route.continue();
  });
}

async function openSettingsApiKeySection(page) {
  await page.getByRole('button', { name: 'Einstellungen' }).click();
  await page.getByRole('link', { name: 'API Keys' }).click();
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

test.describe('Codex connection settings card (TASK-CHATGPT-DEVICE-CODE-PROVIDER.2)', () => {
  test.describe.configure({ mode: 'serial', timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    codexState = { ...disconnectedState };
    verifiedChatgptModels = [];
    modelVerificationFailed = false;
    openedVerificationUrls = [];
    loginFailure = false;
    nextStatusState = null;
    replacementCompletionState = null;
    logoutRequests = 0;
    lastUsedModelState = { provider: 'openai', model: 'gpt-3.5-turbo' };

    await page.addInitScript(() => {
      window.__openedCodexVerificationUrls = [];
      window.open = (url) => {
        window.__openedCodexVerificationUrls.push(url);
        return null;
      };
      window.electron = {
        openExternalLink: async (url) => {
          window.__openedCodexVerificationUrls.push(url);
        },
      };
    });

    const { config } = loadJanusAppDataConfig();
    await installInternalApiKeyRoute(page, config.api_key);
    await installCodexConnectionMocks(page);

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

  });

  test('shows separate disconnected card without mutating API key form', async ({ page }) => {
    await openSettingsApiKeySection(page);

    const apiKeySection = page.locator('#api-key-section');
    await expect(apiKeySection.getByRole('heading', { name: 'API Key Verwaltung' })).toBeVisible();
    await expect(apiKeySection.locator('#api-key-form')).toBeVisible();
    await expect(apiKeySection.locator('#codex-connection-card')).toBeVisible();
    await expect(
      apiKeySection.getByRole('heading', { name: 'ChatGPT über Codex' })
    ).toBeVisible();
    await expect(page.getByRole('button', { name: 'Mit ChatGPT anmelden' })).toBeVisible();
  });

  test('shows a transient official device code and opens only the official verification URL', async ({ page }) => {
    await openSettingsApiKeySection(page);
    await page.getByRole('button', { name: 'Mit ChatGPT anmelden' }).click();
    await expect(page.getByText('Anmeldung läuft')).toBeVisible();

    await expect(page.locator('#codex-device-code-instructions')).toContainText('E2E-CODE');
    await expect(page.locator('#codex-device-verification-link')).toHaveAttribute(
      'href',
      'https://auth.openai.com/codex/device'
    );
    const opened = await page.evaluate(() => window.__openedCodexVerificationUrls);
    expect(opened).toEqual(['https://auth.openai.com/codex/device']);
  });

  test('rejects non-HTTPS login URLs before browser open', async ({ page }) => {
    await page.route('**/api/codex-connection/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          verification_url: 'http://evil.example/login',
          user_code: 'E2E-CODE',
          login_id: 'login-e2e-bad',
          codex_connection: {
            ...disconnectedState,
            connection_state: 'connecting',
            login_pending: true,
            login_id: 'login-e2e-bad',
          },
        }),
      });
    });

    await openSettingsApiKeySection(page);
    await page.getByRole('button', { name: 'Mit ChatGPT anmelden' }).click();
    await expect(page.locator('#codex-connection-error')).toContainText('Ungültige Anmelde-URL');

    await expect(page.locator('#codex-device-code-instructions')).toBeHidden();
    const opened = await page.evaluate(() => window.__openedCodexVerificationUrls);
    expect(opened).toEqual([]);
  });

  test('supports pending first-login cancellation', async ({ page }) => {
    await openSettingsApiKeySection(page);
    await page.getByRole('button', { name: 'Mit ChatGPT anmelden' }).click();
    await expect(page.getByRole('button', { name: 'Anmeldung abbrechen' })).toBeVisible();
    await page.getByRole('button', { name: 'Anmeldung abbrechen' }).click();
    await expect(page.getByRole('button', { name: 'Mit ChatGPT anmelden' })).toBeVisible();
  });

  test('preserves the connected Janus account through cancel and replaces it only after completion', async ({ page }) => {
    codexState = { ...connectedState };
    await openSettingsApiKeySection(page);
    await expect(page.getByText('Mit ChatGPT verbunden')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText('user@example.com')).toBeVisible();
    await expect(page.getByText('Default Workspace')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Konto wechseln' })).toBeVisible();

    await page.getByRole('button', { name: 'Konto wechseln' }).click();
    await expect(page.getByText('Anmeldung läuft')).toBeVisible();
    await expect(page.getByText('user@example.com')).toBeVisible();
    await page.getByRole('button', { name: 'Anmeldung abbrechen' }).click();
    await expect(page.getByText('Mit ChatGPT verbunden')).toBeVisible();
    await expect(page.getByText('user@example.com')).toBeVisible();

    replacementCompletionState = {
      ...connectedState,
      account_identifier: 'second@example.com',
      workspace_id: 'ws-second',
      workspace_display: 'Second Workspace',
    };
    await page.getByRole('button', { name: 'Konto wechseln' }).click();
    await expect(page.getByText('second@example.com')).toBeVisible({ timeout: 15_000 });
    expect(logoutRequests).toBe(0);

    await page.getByRole('button', { name: 'Abmelden' }).click();
    await expect(page.getByRole('button', { name: 'Mit ChatGPT anmelden' })).toBeVisible();
    expect(logoutRequests).toBe(1);
  });

  test('supports retry from an unavailable runtime state', async ({ page }) => {
    codexState = {
      ...disconnectedState,
      connection_state: 'unavailable',
      retry_reason: 'runtime_unavailable',
    };
    await openSettingsApiKeySection(page);
    await expect(page.getByText('ChatGPT ist derzeit nicht verfügbar')).toBeVisible({ timeout: 15_000 });
    await page.getByRole('button', { name: 'Erneut versuchen' }).click();
    await expect(page.getByRole('button', { name: 'Mit ChatGPT anmelden' })).toBeVisible();
  });

  test('keeps the old Janus account after a failed replacement login', async ({ page }) => {
    codexState = { ...connectedState };
    await openSettingsApiKeySection(page);
    loginFailure = true;

    await page.getByRole('button', { name: 'Konto wechseln' }).click();

    await expect(page.locator('#codex-connection-error')).toContainText('ChatGPT ist derzeit nicht verfügbar');
    await expect(page.getByText('Mit ChatGPT verbunden')).toBeVisible();
    await expect(page.getByText('user@example.com')).toBeVisible();
  });

  test('disables login when secure persistence is unavailable', async ({ page }) => {
    codexState = {
      ...disconnectedState,
      connection_state: 'unavailable',
      retry_reason: 'isolation_evidence_pending',
      capabilities: {
        managed_chatgpt_login: false,
        keyring_only: true,
        janus_isolated: false,
      },
    };
    await openSettingsApiKeySection(page);

    await expect(page.getByRole('button', { name: 'Anmeldung nicht verfügbar' })).toBeDisabled();
    await expect(page.getByText('Janus verwendet keine alternative Speicherung')).toBeVisible();
  });

  test('shows only currently verified ChatGPT models and fails closed on verification loss', async ({ page }) => {
    codexState = { ...connectedState };
    // Wait for the real app initialization and its models-updated listener.
    await openSettingsApiKeySection(page);
    verifiedChatgptModels = [
      { id: 'gpt-verified', name: 'Verified model', provider: 'chatgpt', type: 'text' },
    ];
    await page.evaluate(() => window.dispatchEvent(new Event('models-updated')));
    // The app refreshes the catalog and selections asynchronously before it
    // re-renders provider/model choices.
    await page.waitForTimeout(100);

    const providerSelect = page.locator('#provider-select');
    await expect(providerSelect.locator('option[value="chatgpt"]')).toHaveCount(1);
    await providerSelect.selectOption('chatgpt');
    await expect(page.locator('#model-select option[value="gpt-verified"]')).toHaveCount(1);

    modelVerificationFailed = true;
    await openSettingsApiKeySection(page);
    await expect(page.locator('#codex-connection-error')).toContainText('Modelle derzeit nicht verfügbar');
    await page.evaluate(() => window.dispatchEvent(new Event('models-updated')));
    await expect(providerSelect.locator('option[value="chatgpt"]')).toHaveCount(0);
  });

  test('self-heals a stale persisted ChatGPT selection when verification is unavailable', async ({ page }) => {
    lastUsedModelState = { provider: 'chatgpt', model: 'gpt-stale' };
    verifiedChatgptModels = [];
    modelVerificationFailed = true;

    const appReady = page.waitForEvent('console', {
      predicate: (message) => message.text().includes('Initialization complete. Janus is ready.'),
      timeout: 30_000,
    });
    await page.reload();
    await appReady;

    const providerSelect = page.locator('#provider-select');
    await expect(providerSelect).not.toHaveValue('');
    await expect(providerSelect).not.toHaveValue('chatgpt');
    await expect(providerSelect.locator('option[value="chatgpt"]')).toHaveCount(0);
  });
});
