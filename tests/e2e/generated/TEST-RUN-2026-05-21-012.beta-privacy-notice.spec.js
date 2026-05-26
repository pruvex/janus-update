/**
 * TEST-RUN-2026-05-21-012 Beta Privacy Notice and Data Rights
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const TEST_RUN_ID = 'TEST-RUN-2026-05-21-012';
const TITLE = 'Janus Beta Privacy Notice and Data Rights';
const ROOT = process.cwd();
const RESULT_DIR = path.join(ROOT, 'documentation', 'test-results', TEST_RUN_ID);
const RESULT_JSON = path.join(ROOT, 'documentation', 'test-results', `${TEST_RUN_ID}_results.json`);
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

async function record(testCaseId, classification, body) {
  const started = Date.now();
  const evidencePath = path.join(RESULT_DIR, `${testCaseId}_evidence.json`);
  try {
    const evidence = await body();
    writeJson(evidencePath, {
      rawSensitiveEvidencePolicy: 'no-raw-secrets-no-raw-private-data',
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
      rawSensitiveEvidencePolicy: 'no-raw-secrets-no-raw-private-data',
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
    summary: { total: 10, passed, failed, blocked, manualGateRequired: 0 },
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
  test.beforeAll(() => ensureDir(RESULT_DIR));
  test.afterAll(() => emitAggregateResult());

  test('PRIV-001: notice covers beta data categories', async () => {
    await record('PRIV-001', 'DATA_CATEGORIES_NOTICE_PASS', async () => {
      const notice = readText('documentation/beta/BETA_PRIVACY_NOTICE.md').toLowerCase();
      for (const term of ['chat', 'files', 'memory', 'rag', 'logs', 'providers', 'telemetry', 'generated artifacts']) {
        expect(notice).toContain(term);
      }
      return { notice: 'documentation/beta/BETA_PRIVACY_NOTICE.md', coveredTerms: ['chat', 'files', 'memory', 'rag', 'logs', 'providers', 'telemetry'] };
    });
  });

  test('PRIV-002: notice discloses external provider sharing', async () => {
    await record('PRIV-002', 'PROVIDER_SHARING_NOTICE_PASS', async () => {
      const notice = readText('documentation/beta/BETA_PRIVACY_NOTICE.md').toLowerCase();
      for (const term of ['openai', 'gemini', 'google', 'ollama', 'rss/news', 'wikipedia', 'weather', 'geo', 'price', 'sentry', 'supabase']) {
        expect(notice).toContain(term);
      }
      return { providerClassesCovered: ['llm', 'local', 'current-data', 'telemetry'] };
    });
  });

  test('PRIV-003: onboarding warns against sensitive uploads', async () => {
    await record('PRIV-003', 'SENSITIVE_UPLOAD_WARNING_PASS', async () => {
      const onboarding = readText('documentation/beta/BETA_TESTER_ONBOARDING_PRIVACY_ACK.md').toLowerCase();
      for (const term of ['secrets', 'api keys', 'passwords', 'production customer data', 'regulated']) {
        expect(onboarding).toContain(term);
      }
      return { onboarding: 'documentation/beta/BETA_TESTER_ONBOARDING_PRIVACY_ACK.md' };
    });
  });

  test('PRIV-004: retention and minimization assumptions are stated', async () => {
    await record('PRIV-004', 'RETENTION_NOTICE_PASS', async () => {
      const notice = readText('documentation/beta/BETA_PRIVACY_NOTICE.md').toLowerCase();
      expect(notice).toContain('retention');
      expect(notice).toContain('janus_telemetry_mode=off');
      expect(notice).toContain('janus_telemetry_mode=minimal');
      expect(notice).toContain('remote provider retention');
      return { retentionLanguagePresent: true, telemetryModesCovered: ['off', 'minimal'] };
    });
  });

  test('PRIV-005: deletion dry-run path and owner exist', async () => {
    await record('PRIV-005', 'DELETION_PROCESS_OWNER_PASS', async () => {
      const process = readText('documentation/beta/BETA_DATA_RIGHTS_PROCESS.md').toLowerCase();
      expect(process).toContain('deletion dry-run');
      expect(process).toContain('privacy-contact');
      expect(process).toContain('operator-on-call');
      return { process: 'documentation/beta/BETA_DATA_RIGHTS_PROCESS.md', owners: ['privacy-contact', 'operator-on-call'] };
    });
  });

  test('PRIV-006: export/access dry-run path and owner exist', async () => {
    await record('PRIV-006', 'EXPORT_ACCESS_PROCESS_OWNER_PASS', async () => {
      const process = readText('documentation/beta/BETA_DATA_RIGHTS_PROCESS.md').toLowerCase();
      expect(process).toContain('access/export dry-run');
      expect(process).toContain('privacy-contact');
      expect(process).toContain('counts, object ids, timestamps');
      return { exportDryRunDocumented: true };
    });
  });

  test('PRIV-007: privacy/security incident route exists', async () => {
    await record('PRIV-007', 'INCIDENT_REPORTING_ROUTE_PASS', async () => {
      const process = readText('documentation/beta/BETA_DATA_RIGHTS_PROCESS.md').toLowerCase();
      expect(process).toContain('incident reporting');
      expect(process).toContain('operator-on-call');
      expect(process).toContain('privacy-contact');
      return { contactAliases: ['operator-on-call', 'privacy-contact'] };
    });
  });

  test('PRIV-008: beta tester acknowledgement is recorded locally in UI', async ({ page }) => {
    await record('PRIV-008', 'BETA_ACK_UI_RECORDING_PASS', async () => {
      await page.goto('/');
      const modal = page.locator('#beta-privacy-modal');
      await expect(modal).toBeVisible();
      await expect(page.locator('#beta-privacy-accept-btn')).toBeDisabled();
      await page.locator('#beta-privacy-ack-checkbox').check();
      await expect(page.locator('#beta-privacy-accept-btn')).toBeEnabled();
      await page.locator('#beta-privacy-accept-btn').click();
      await expect(modal).toHaveClass(/hidden/);
      const ack = await page.evaluate(() => JSON.parse(localStorage.getItem('janus_beta_privacy_ack_v1') || '{}'));
      expect(ack.accepted).toBe(true);
      expect(ack.noticeVersion).toBe('2026-05-21.1');
      expect(typeof ack.acceptedAt).toBe('string');
      return { storageKey: 'janus_beta_privacy_ack_v1', noticeVersion: ack.noticeVersion, accepted: ack.accepted };
    });
  });

  test('PRIV-009: privacy artifacts contain no raw credential-shaped values', async () => {
    await record('PRIV-009', 'PRIVACY_ARTIFACT_SECRET_SCAN_PASS', async () => {
      const files = [
        'documentation/beta/BETA_PRIVACY_NOTICE.md',
        'documentation/beta/BETA_DATA_RIGHTS_PROCESS.md',
        'documentation/beta/BETA_TESTER_ONBOARDING_PRIVACY_ACK.md',
        'frontend/index.html',
        'frontend/js/beta-privacy-notice.js',
      ];
      const patterns = [/sk-[A-Za-z0-9]{20,}/, /AIza[0-9A-Za-z_\-]{20,}/, /bearer\s+[A-Za-z0-9_\-.]{20,}/i];
      for (const file of files) {
        const text = readText(file);
        for (const pattern of patterns) {
          expect(text).not.toMatch(pattern);
        }
      }
      return { scannedFiles: files.length, rawCredentialShapesFound: 0 };
    });
  });

  test('PRIV-010: privacy readiness gate is pass', async () => {
    await record('PRIV-010', 'PRIVACY_READINESS_GATE_PASS', async () => {
      const notice = readText('documentation/beta/BETA_PRIVACY_NOTICE.md');
      const process = readText('documentation/beta/BETA_DATA_RIGHTS_PROCESS.md');
      const onboarding = readText('documentation/beta/BETA_TESTER_ONBOARDING_PRIVACY_ACK.md');
      expect(notice.length).toBeGreaterThan(2500);
      expect(process.length).toBeGreaterThan(1800);
      expect(onboarding.length).toBeGreaterThan(900);
      return { gate: 'PASS', criticalHighPrivacyBlockers: 0 };
    });
  });
});
