import { expect, test } from '@playwright/test';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';


const SENTINEL_A = 'TEST_OPENROUTER_SECRET_ALPHA';
const SENTINEL_B = 'TEST_OPENROUTER_SECRET_BETA';
const OPENROUTER_MODEL_A = 'anthropic/claude-3.7-sonnet-20250219';
const OPENROUTER_MODEL_B = 'qwen/qwen3-235b-a22b-2507';


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

async function installOpenRouterSelectionRoutes(page, state) {
  await page.route('**/api/models/catalog', async (route) => {
    const openrouterModels = state.certifiedModels.map((id) => ({
      id,
      name: id,
      provider: 'openrouter',
      type: 'text',
      model_version: id.split('/').at(-1),
    }));
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
        ...openrouterModels,
      ]),
    });
  });

  await page.route('**/api/models/openrouter/eligibility', async (route) => {
    const keyPresent = state.keyState !== 'MISSING';
    const eligible = state.keyState === 'VALID' && state.certifiedModels.length > 0;
    const reason = !keyPresent
      ? 'key_missing'
      : state.keyState === 'INVALID'
        ? 'key_invalid'
        : state.keyState !== 'VALID'
          ? 'key_unverified'
          : state.certifiedModels.length === 0
            ? 'no_certified_models'
            : 'eligible';
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        provider: 'openrouter',
        key_present: keyPresent,
        key_state: keyPresent ? state.keyState : 'UNVERIFIED',
        eligible,
        reason,
        models: [...state.certifiedModels],
      }),
    });
  });

  await page.route('**/api/models/selection/**', async (route) => {
    const provider = new URL(route.request().url()).pathname.split('/').at(-1);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        selected_models: provider === 'openai' ? ['gpt-5.4-mini'] : [],
      }),
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
    if (route.request().method() === 'PUT') {
      state.lastUsed = route.request().postDataJSON();
      state.lastUsedWrites.push({ ...state.lastUsed });
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(state.lastUsed),
    });
  });

  await page.route('**/api/keys', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        api_keys: {
          openai: '********',
          openrouter: {
            present: state.keyState !== 'MISSING',
            masked: state.keyState !== 'MISSING' ? '********' : null,
            state: state.keyState === 'MISSING' ? 'UNVERIFIED' : state.keyState,
          },
        },
      }),
    });
  });

  await page.route('**/api/codex-connection', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        available: true,
        codex_connection: {
          connection_state: 'disconnected',
          capabilities: {
            managed_chatgpt_login: true,
            keyring_only: true,
            janus_isolated: true,
          },
        },
      }),
    });
  });

  await page.route('**/api/chats?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([state.chat]),
    });
  });
  await page.route('**/api/chats/1/messages', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });
  await page.route('**/api/chats/1/llm', async (route) => {
    const payload = route.request().postDataJSON();
    state.chat.header_provider = payload.provider;
    state.chat.header_model = payload.model;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(state.chat),
    });
  });
  await page.route('**/api/chats/1', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(state.chat),
    });
  });
  await page.route('**/api/chat/stream', async (route) => {
    state.streamRequests += 1;
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'unexpected OpenRouter transmission' }),
    });
  });
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
    await page.reload();
    await expect(page.getByRole('button', { name: 'Einstellungen' })).toBeVisible({
      timeout: 30_000,
    });
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

test.describe('OpenRouter retained provider/model selection (TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4)', () => {
  test.describe.configure({ mode: 'serial', timeout: 90_000 });

  test('requires deliberate selection and retains disabled sidebar and window choices', async ({ page }) => {
    const state = {
      keyState: 'VALID',
      certifiedModels: [OPENROUTER_MODEL_A, OPENROUTER_MODEL_B],
      lastUsed: { provider: 'openai', model: 'gpt-5.4-mini' },
      lastUsedWrites: [],
      chat: {
        id: 1,
        title: 'OpenRouter Auswahltest',
        project_id: null,
        is_archived: false,
        header_provider: null,
        header_model: null,
      },
      streamRequests: 0,
    };

    const { config } = loadJanusAppDataConfig();
    await installInternalApiKeyRoute(page, config.api_key);
    await installOpenRouterSelectionRoutes(page, state);
    const token = createE2eJwt();
    await page.addInitScript(({ jwt }) => {
      localStorage.clear();
      localStorage.setItem('auth_token', jwt);
      localStorage.setItem(
        'janus_beta_privacy_ack_v1',
        JSON.stringify({
          accepted: true,
          noticeVersion: '2026-07-17.1',
          acceptedAt: new Date().toISOString(),
        }),
      );
      localStorage.setItem(
        'janus_window_workspace_v1',
        JSON.stringify({
          v: 1,
          activeWindowId: 'A',
          chatA: 1,
          chatB: null,
          isOpenB: true,
        }),
      );
    }, { jwt: token });

    await page.goto('http://localhost:5173/');
    await expect(page.getByRole('button', { name: 'Einstellungen' })).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.locator('#beta-privacy-modal')).toContainText(
      'über OpenRouter an den ausgewählten Modellanbieter',
    );

    const providerSelect = page.locator('#provider-select');
    const modelSelect = page.locator('#model-select');
    const sendButtonA = page.locator('#send-button-A');

    await expect(providerSelect.locator('option[value="openrouter"]')).toBeEnabled({
      timeout: 30_000,
    });
    const writesBeforeOpenRouter = state.lastUsedWrites.length;
    await providerSelect.selectOption('openrouter');
    await expect(modelSelect).toHaveValue('');
    expect(state.lastUsedWrites.length).toBe(writesBeforeOpenRouter);

    await modelSelect.selectOption(OPENROUTER_MODEL_A);
    await expect(sendButtonA).toBeEnabled();
    expect(state.lastUsed).toEqual({
      provider: 'openrouter',
      model: OPENROUTER_MODEL_A,
    });

    const writesBeforeInvalidReload = state.lastUsedWrites.length;
    state.keyState = 'INVALID';
    await page.reload();
    await expect(page.getByRole('button', { name: 'Einstellungen' })).toBeVisible({
      timeout: 30_000,
    });
    await expect(providerSelect).toHaveValue('openrouter');
    await expect(providerSelect.locator('option[value="openrouter"]')).toBeDisabled();
    await expect(modelSelect).toHaveValue(OPENROUTER_MODEL_A);
    await expect(modelSelect).toBeDisabled();
    await expect(sendButtonA).toBeDisabled();
    await expect(page.locator('#openrouter-chat-eligibility')).toContainText(
      'Der API-Key ist ungültig',
    );
    expect(state.lastUsedWrites.length).toBe(writesBeforeInvalidReload);

    await page.evaluate(() => {
      document.getElementById('chat-form-A')?.dispatchEvent(
        new Event('submit', { bubbles: true, cancelable: true }),
      );
    });
    await page.waitForTimeout(200);
    expect(state.streamRequests).toBe(0);

    state.keyState = 'VALID';
    state.certifiedModels = [OPENROUTER_MODEL_B];
    await page.reload();
    await expect(page.getByRole('button', { name: 'Einstellungen' })).toBeVisible({
      timeout: 30_000,
    });
    await expect(providerSelect).toHaveValue('openrouter');
    await expect(modelSelect).toHaveValue(OPENROUTER_MODEL_A);
    await expect(modelSelect.locator(`option[value="${OPENROUTER_MODEL_A}"]`)).toBeDisabled();
    await expect(modelSelect.locator(`option[value="${OPENROUTER_MODEL_B}"]`)).toBeEnabled();
    await expect(sendButtonA).toBeDisabled();

    await modelSelect.selectOption(OPENROUTER_MODEL_B);
    await expect(sendButtonA).toBeEnabled();
    expect(state.lastUsed).toEqual({
      provider: 'openrouter',
      model: OPENROUTER_MODEL_B,
    });

    await providerSelect.selectOption('openai');
    await expect(providerSelect).toHaveValue('openai');
    const headerProvider = page.locator('#chat-header-provider-A');
    const headerModel = page.locator('#chat-header-model-A');
    await headerProvider.selectOption('openrouter');
    await expect(headerModel).toHaveValue('');
    await headerModel.selectOption(OPENROUTER_MODEL_B);
    await expect(sendButtonA).toBeEnabled();
    expect(state.chat.header_provider).toBe('openrouter');
    expect(state.chat.header_model).toBe(OPENROUTER_MODEL_B);

    state.keyState = 'UNVERIFIED';
    await page.reload();
    await expect(page.getByRole('button', { name: 'Einstellungen' })).toBeVisible({
      timeout: 30_000,
    });
    await expect(providerSelect).toHaveValue('openai');
    await expect(headerProvider).toHaveValue('openrouter');
    await expect(headerProvider.locator('option[value="openrouter"]')).toBeDisabled();
    await expect(headerModel).toHaveValue(OPENROUTER_MODEL_B);
    await expect(headerModel).toBeDisabled();
    await expect(sendButtonA).toBeDisabled();
    expect(state.streamRequests).toBe(0);
  });
});
