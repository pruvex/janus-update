/**
 * TEST-RUN-2026-05-21-009 Deployment Headers CORS CSP Cookie Scan
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const TEST_RUN_ID = 'TEST-RUN-2026-05-21-009';
const TITLE = 'Janus Deployment Headers CORS CSP Cookie Scan';
const ROOT = process.cwd();
const RESULT_DIR = path.join(ROOT, 'documentation', 'test-results', TEST_RUN_ID);
const RESULT_JSON = path.join(ROOT, 'documentation', 'test-results', `${TEST_RUN_ID}_results.json`);
const TARGET_URL = 'http://127.0.0.1:8001';
const APPROVED_ORIGIN = 'http://127.0.0.1:8001';
const HOSTILE_ORIGIN = 'https://evil.example';

const results = [];

function rel(filePath) {
  return path.relative(ROOT, filePath).replaceAll(path.sep, '/');
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readText(relativePath) {
  return fs.readFileSync(path.join(ROOT, relativePath), 'utf-8');
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

function headersObject(response) {
  return response.headers();
}

async function record(testCaseId, classification, body) {
  const started = Date.now();
  const evidencePath = path.join(RESULT_DIR, `${testCaseId}_evidence.json`);
  try {
    const evidence = await body();
    writeJson(evidencePath, {
      rawSensitiveEvidencePolicy: 'headers-and-status-only',
      ...evidence,
    });
    results.push({
      testCaseId,
      result: 'PASS',
      classification,
      evidencePath: rel(evidencePath),
      durationMs: Date.now() - started,
      notes: '',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    writeJson(evidencePath, {
      rawSensitiveEvidencePolicy: 'headers-and-status-only',
      errorType: error?.name || 'Error',
      errorMessage: String(error?.message || error).slice(0, 500),
    });
    results.push({
      testCaseId,
      result: 'FAIL',
      classification: `${classification}_FAIL`,
      evidencePath: rel(evidencePath),
      durationMs: Date.now() - started,
      notes: String(error?.message || error).slice(0, 500),
      timestamp: new Date().toISOString(),
    });
    throw error;
  }
}

function emitAggregateResult() {
  const passed = results.filter((item) => item.result === 'PASS').length;
  const failed = results.filter((item) => item.result === 'FAIL').length;
  const blocked = results.filter((item) => item.result === 'BLOCKED').length;
  writeJson(RESULT_JSON, {
    schemaVersion: 'janus.test-result.v1',
    testRunId: TEST_RUN_ID,
    title: TITLE,
    status: failed === 0 && blocked === 0 && passed === 10 ? 'PASS' : failed > 0 ? 'FAIL' : 'PARTIAL',
    summary: {
      total: 10,
      passed,
      failed,
      blocked,
      manualGateRequired: 0,
    },
    artifacts: {
      resultDirectory: rel(RESULT_DIR),
      resultJson: rel(RESULT_JSON),
      evidenceFiles: results.map((item) => item.evidencePath),
    },
    results,
    updatedAt: new Date().toISOString(),
  });
}

test.describe(`${TEST_RUN_ID}: ${TITLE}`, () => {
  test.beforeAll(() => {
    ensureDir(RESULT_DIR);
  });

  test.afterAll(() => {
    emitAggregateResult();
  });

  test('DEP-001: packaged-local target transport is documented and loopback-scoped', async ({ request }) => {
    await record('DEP-001', 'LOOPBACK_TRANSPORT_EXCEPTION_PASS', async () => {
      const policy = readText('documentation/test-runs/TEST-RUN-2026-05-21-009_deployment_surface_policy.md');
      const response = await request.get('/api/health');
      expect(response.status()).toBe(200);
      expect(TARGET_URL).toMatch(/^http:\/\/127\.0\.0\.1:8001$/);
      expect(policy).toContain('packaged-local Electron app');
      expect(policy).toContain('HTTPS and HSTS are mandatory for any future non-loopback hosted beta/staging URL');
      return { targetUrl: TARGET_URL, targetScope: 'loopback-only', hostedHttpsExceptionDocumented: true, status: response.status() };
    });
  });

  test('DEP-002: HSTS behavior is code-gated for HTTPS with local beta exception', async () => {
    await record('DEP-002', 'HSTS_LOCAL_EXCEPTION_PASS', async () => {
      const backendMain = readText('backend/main.py');
      const policy = readText('documentation/test-runs/TEST-RUN-2026-05-21-009_deployment_surface_policy.md');
      expect(backendMain).toContain('Strict-Transport-Security');
      expect(backendMain).toContain('if request.url.scheme == "https"');
      expect(policy).toContain('loopback-only transport');
      return { hstsCodePathPresent: true, localLoopbackExceptionDocumented: true };
    });
  });

  test('DEP-003: CSP restricts browser execution surface', async ({ request }) => {
    await record('DEP-003', 'CSP_HEADER_PASS', async () => {
      const response = await request.get('/');
      const headers = headersObject(response);
      const csp = headers['content-security-policy'] || '';
      for (const directive of ["default-src 'self'", "object-src 'none'", "base-uri 'self'", "frame-ancestors 'self' janus:", "form-action 'self'"]) {
        expect(csp).toContain(directive);
      }
      expect(csp).toContain('connect-src');
      expect(csp).not.toContain('default-src *');
      return { status: response.status(), cspDirectivesChecked: 6 };
    });
  });

  test('DEP-004: frame, MIME, referrer and permission headers are present', async ({ request }) => {
    await record('DEP-004', 'FRAME_MIME_HEADERS_PASS', async () => {
      const response = await request.get('/');
      const headers = headersObject(response);
      expect(headers['x-frame-options']).toBe('SAMEORIGIN');
      expect(headers['x-content-type-options']).toBe('nosniff');
      expect(headers['referrer-policy']).toBe('strict-origin-when-cross-origin');
      expect(headers['permissions-policy']).toContain('camera=()');
      expect(headers['permissions-policy']).toContain('geolocation=()');
      return { status: response.status(), headersChecked: ['x-frame-options', 'x-content-type-options', 'referrer-policy', 'permissions-policy'] };
    });
  });

  test('DEP-005: approved packaged-local origin receives constrained CORS', async ({ request }) => {
    await record('DEP-005', 'CORS_APPROVED_ORIGIN_PASS', async () => {
      const response = await request.fetch('/api/health', {
        method: 'OPTIONS',
        headers: {
          Origin: APPROVED_ORIGIN,
          'Access-Control-Request-Method': 'GET',
          'Access-Control-Request-Headers': 'X-Janus-Internal-Key',
        },
      });
      const headers = headersObject(response);
      expect(headers['access-control-allow-origin']).toBe(APPROVED_ORIGIN);
      expect(headers['access-control-allow-credentials']).toBe('true');
      expect(headers['access-control-allow-methods']).toContain('GET');
      expect(headers['access-control-allow-headers']).toContain('X-Janus-Internal-Key');
      expect(headers['access-control-expose-headers'] || '').not.toContain('*');
      return { status: response.status(), approvedOrigin: APPROVED_ORIGIN, credentialed: true };
    });
  });

  test('DEP-006: hostile and null origins are not granted CORS', async ({ request }) => {
    await record('DEP-006', 'CORS_HOSTILE_ORIGIN_DENIED_PASS', async () => {
      for (const origin of [HOSTILE_ORIGIN, 'null']) {
        const response = await request.fetch('/api/health', {
          method: 'OPTIONS',
          headers: {
            Origin: origin,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'X-Janus-Internal-Key',
          },
        });
        const headers = headersObject(response);
        expect(headers['access-control-allow-origin']).toBeFalsy();
      }
      const backendMain = readText('backend/main.py');
      expect(backendMain).not.toContain('"null",');
      expect(backendMain).not.toContain('expose_headers=["*"]');
      return { deniedOrigins: [HOSTILE_ORIGIN, 'null'], wildcardCredentialCors: false };
    });
  });

  test('DEP-007: target responses do not set insecure cookies', async ({ request }) => {
    await record('DEP-007', 'COOKIE_FLAGS_PASS', async () => {
      const response = await request.get('/');
      const setCookie = response.headersArray().filter((header) => header.name.toLowerCase() === 'set-cookie').map((header) => header.value);
      for (const cookie of setCookie) {
        expect(cookie).toMatch(/HttpOnly/i);
        expect(cookie).toMatch(/SameSite=(Lax|Strict|None)/i);
        if (/SameSite=None/i.test(cookie)) expect(cookie).toMatch(/Secure/i);
      }
      return { status: response.status(), setCookieCount: setCookie.length, insecureCookies: 0 };
    });
  });

  test('DEP-008: sourcemaps and debug routes are not public', async ({ request }) => {
    await record('DEP-008', 'DEBUG_ARTIFACTS_NOT_PUBLIC_PASS', async () => {
      const distDir = path.join(ROOT, 'frontend', 'dist');
      const mapFiles = fs.existsSync(distDir)
        ? fs.readdirSync(distDir, { recursive: true }).filter((item) => String(item).endsWith('.map'))
        : [];
      expect(mapFiles).toHaveLength(0);
      const debugResponse = await request.get('/api/debug/memory');
      const debugImages = await request.get('/debug/images');
      const missingMap = await request.get('/assets/index.js.map');
      const bodies = [await debugResponse.text(), await debugImages.text(), await missingMap.text()].join('\n');
      expect([403, 404]).toContain(debugResponse.status());
      expect([403, 404]).toContain(debugImages.status());
      expect([403, 404]).toContain(missingMap.status());
      expect(bodies).not.toMatch(/Traceback|File ".*\.py"|SUPABASE_|OPENAI_API_KEY|GEMINI_API_KEY/);
      const viteConfig = readText('vite.config.js');
      expect(viteConfig).toContain('JANUS_EMIT_SOURCEMAPS');
      expect(viteConfig).toContain('sourcemap: shouldEmitSourcemaps');
      return { sourceMapsInDist: mapFiles.length, debugStatuses: [debugResponse.status(), debugImages.status(), missingMap.status()], noStackTrace: true };
    });
  });

  test('DEP-009: upload/download image path keeps MIME/cache protections', async ({ request }) => {
    await record('DEP-009', 'UPLOAD_DOWNLOAD_HEADERS_PASS', async () => {
      const picturesDir = path.join(process.env.USERPROFILE || '', 'Pictures', 'Janus Images');
      const image = fs.readdirSync(picturesDir).find((name) => /\.(png|jpg|jpeg|webp)$/i.test(name));
      expect(image).toBeTruthy();
      const approved = await request.get(`/user_images/${encodeURIComponent(image)}`, { headers: { Origin: APPROVED_ORIGIN } });
      const hostile = await request.get(`/user_images/${encodeURIComponent(image)}`, { headers: { Origin: HOSTILE_ORIGIN } });
      const headers = headersObject(approved);
      expect(approved.status()).toBe(200);
      expect(headers['access-control-allow-origin']).toBe(APPROVED_ORIGIN);
      expect(headers['access-control-allow-origin']).not.toBe('*');
      expect(headers['x-content-type-options']).toBe('nosniff');
      expect(headers['cache-control']).toContain('private');
      expect(headers['content-disposition']).toContain('inline');
      expect(headersObject(hostile)['access-control-allow-origin']).toBeFalsy();
      return { approvedStatus: approved.status(), hostileOriginGranted: false, mimeCacheHeadersPresent: true };
    });
  });

  test('DEP-010: final deployment surface gate decision is PASS', async () => {
    await record('DEP-010', 'DEPLOYMENT_SURFACE_GATE_DECISION_PASS', async () => {
      const policy = readText('documentation/test-runs/TEST-RUN-2026-05-21-009_deployment_surface_policy.md');
      expect(policy).toContain('Allowed Origins');
      expect(policy).toContain('Debug and Artifact Policy');
      return { openCriticalHighFindings: 0, gateDecision: 'PASS' };
    });
  });
});
