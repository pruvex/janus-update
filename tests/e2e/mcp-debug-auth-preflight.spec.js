import { expect, test } from '@playwright/test';

test.describe('MCP debug auth preflight', () => {
  test('installs local debug auth without exposing the internal API key', async ({ page }) => {
    const failedResponses = [];
    page.on('response', (response) => {
      if (response.status() === 401 && response.url().includes('/api/personalities')) {
        failedResponses.push(response.url());
      }
    });

    await page.goto('/');

    const preflight = await page.evaluate(async () => {
      const response = await fetch(`${window.API_BASE_URL}/api/debug/mcp/auth-preflight`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const payload = await response.json();
      localStorage.setItem('auth_token', payload.storage.auth_token);
      localStorage.setItem('janus_mcp_debug_session', payload.storage.janus_mcp_debug_session);
      return {
        status: response.status,
        tokenType: payload.token_type,
        hasInternalApiKey: Object.keys(payload).some((key) => key.toLowerCase().includes('api_key')),
        boundaries: payload.security_boundaries,
      };
    });

    expect(preflight.status).toBe(200);
    expect(preflight.tokenType).toBe('janus_mcp_debug_session');
    expect(preflight.hasInternalApiKey).toBe(false);
    expect(preflight.boundaries).toContain('no-internal-api-key-export');
    expect(preflight.boundaries).toContain('no-external-origin');
    failedResponses.length = 0;

    const personalities = await page.evaluate(async () => {
      const response = await fetch(`${window.API_BASE_URL}/api/personalities`);
      return { status: response.status, ok: response.ok };
    });

    const activePersonality = await page.evaluate(async () => {
      const response = await fetch(`${window.API_BASE_URL}/api/personalities/active`);
      return { status: response.status, ok: response.ok };
    });

    expect(personalities).toEqual({ status: 200, ok: true });
    expect(activePersonality).toEqual({ status: 200, ok: true });
    expect(failedResponses).toEqual([]);
  });
});
