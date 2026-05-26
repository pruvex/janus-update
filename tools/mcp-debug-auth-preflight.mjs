import { chromium } from '@playwright/test';

const targetUrl = process.argv[2] || process.env.JANUS_MCP_TARGET_URL || 'http://localhost:5173';
const apiBaseUrl = process.env.JANUS_API_BASE_URL || 'http://127.0.0.1:8001';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

try {
  await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });

  const result = await page.evaluate(async (baseUrl) => {
    const response = await fetch(`${baseUrl}/api/debug/mcp/auth-preflight`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        text: await response.text(),
      };
    }

    const payload = await response.json();
    localStorage.setItem('auth_token', payload.storage.auth_token);
    localStorage.setItem('janus_mcp_debug_session', payload.storage.janus_mcp_debug_session);
    return {
      ok: true,
      expiresInMinutes: payload.expires_in_minutes,
      boundaries: payload.security_boundaries,
    };
  }, apiBaseUrl);

  if (!result.ok) {
    throw new Error(`MCP auth preflight failed with ${result.status}: ${result.text}`);
  }

  await page.reload({ waitUntil: 'domcontentloaded' });

  const verification = await page.evaluate(async (baseUrl) => {
    const debugSession = localStorage.getItem('janus_mcp_debug_session');
    const response = await fetch(`${baseUrl}/api/personalities`, {
      headers: { 'X-Janus-MCP-Debug-Session': debugSession || '' },
    });
    return { status: response.status, ok: response.ok };
  }, apiBaseUrl);

  if (!verification.ok) {
    throw new Error(`MCP auth verification failed with ${verification.status}`);
  }

  console.log(`MCP auth preflight installed for ${targetUrl}.`);
  console.log(`Session expires in ${result.expiresInMinutes} minutes.`);
  console.log(`Security boundaries: ${result.boundaries.join(', ')}`);
} finally {
  await browser.close();
}
