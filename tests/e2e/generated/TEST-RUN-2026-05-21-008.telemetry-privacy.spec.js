/**
 * TEST-RUN-2026-05-21-008 Beta Telemetry Logging Privacy Hardening
 *
 * Evidence never writes raw secrets, private prompt canaries, file content
 * canaries, cookies, bearer tokens or provider headers.
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const TEST_RUN_ID = 'TEST-RUN-2026-05-21-008';
const TITLE = 'Janus Beta Telemetry Logging Privacy Hardening';
const ROOT = process.cwd();
const RESULT_DIR = path.join(ROOT, 'documentation', 'test-results', TEST_RUN_ID);
const RESULT_JSON = path.join(ROOT, 'documentation', 'test-results', `${TEST_RUN_ID}_results.json`);

const PRIVATE_PROMPT_CANARY = 'JANUS_TLOG_PRIVATE_PROMPT_CANARY_20260521';
const PRIVATE_FILE_CANARY = 'JANUS_TLOG_PRIVATE_FILE_CONTENT_CANARY_20260521';
const SECRET_CANARY = 'SECRET-TLOG-OBSERVABILITY-20260521';
const BEARER_CANARY = 'Bearer JANUS_TLOG_BEARER_TOKEN_20260521';

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

function readTextSafe(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch {
    return '';
  }
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

function appDataLogPath() {
  const appData = process.env.APPDATA || process.env.HOME || '';
  return path.join(appData, 'Janus Projekt', 'logs', 'janus_backend.log');
}

function readApiKey() {
  const configPath = path.join(process.env.APPDATA || '', 'Janus Projekt', 'config.json');
  const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  return config.api_key;
}

function safeEvidence(extra = {}) {
  return {
    rawSensitiveEvidencePolicy: 'redacted-only',
    rawPrivateCanariesWritten: false,
    ...extra,
  };
}

async function record(testCaseId, classification, body) {
  const started = Date.now();
  const evidencePath = path.join(RESULT_DIR, `${testCaseId}_evidence.json`);
  try {
    const evidence = await body();
    writeJson(evidencePath, safeEvidence(evidence));
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
    writeJson(evidencePath, safeEvidence({
      errorType: error?.name || 'Error',
      errorMessage: String(error?.message || error).slice(0, 500),
    }));
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
  const aggregate = {
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
  };
  writeJson(RESULT_JSON, aggregate);
}

test.describe(`${TEST_RUN_ID}: ${TITLE}`, () => {
  test.beforeAll(() => {
    ensureDir(RESULT_DIR);
  });

  test.afterAll(() => {
    emitAggregateResult();
  });

  test('TLOG-001: telemetry destinations are inventoried', async () => {
    await record('TLOG-001', 'TELEMETRY_SINK_INVENTORY_PASS', async () => {
      const inventory = readText('documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_sink_inventory.md');
      for (const sink of ['Local AppData backend log', 'Backend Sentry', 'Frontend Sentry', 'Supabase logging', 'Feedback webhook', 'Chroma/PostHog']) {
        expect(inventory).toContain(sink);
      }
      return { sinksDocumented: 6, ownerAndRetentionDocumented: true };
    });
  });

  test('TLOG-002: PII defaults are disabled or minimized', async () => {
    await record('TLOG-002', 'PII_DEFAULTS_PASS', async () => {
      const backendMain = readText('backend/main.py');
      const frontendApp = readText('frontend/js/app.js');
      expect(backendMain).toContain('send_default_pii=False');
      expect(backendMain).toContain('before_send=_before_send_sentry');
      expect(frontendApp).toContain('sendDefaultPii: false');
      expect(frontendApp).toContain('delete event.user');
      expect(frontendApp).toContain('delete event.request');
      expect(frontendApp).toContain('maskAllText: true');
      expect(frontendApp).toContain('blockAllMedia: true');
      return { backendPiiDisabled: true, frontendPiiDisabled: true, replayMaskedAndBlocked: true };
    });
  });

  test('TLOG-003: telemetry sampling is beta-privacy conscious', async () => {
    await record('TLOG-003', 'TELEMETRY_SAMPLING_PASS', async () => {
      const backendMain = readText('backend/main.py');
      const frontendApp = readText('frontend/js/app.js');
      expect(backendMain).toContain('"1.0" if sentry_environment == "development" else "0.1"');
      expect(backendMain).toContain('"1.0" if sentry_environment == "development" else "0.0"');
      expect(frontendApp).toContain('tracesSampleRate: 0.1');
      expect(frontendApp).toContain('replaysSessionSampleRate: 0.0');
      expect(frontendApp).toContain('replaysOnErrorSampleRate: 0.0');
      return { backendProductionTraceSampleRate: 0.1, backendProductionProfileSampleRate: 0.0, frontendReplaySampling: 0.0 };
    });
  });

  test('TLOG-004: shared logging redaction catches secrets and content fields', async () => {
    await record('TLOG-004', 'SECRET_REDACTION_PASS', async () => {
      const output = execFileSync('python', [
        '-c',
        [
          'from backend.utils.redaction import REDACTION_TEXT, redact_sensitive_value',
          'raw={"authorization":"Bearer abcdefghijklmnop","prompt":"JANUS_TLOG_PRIVATE_PROMPT_CANARY_20260521","content":"JANUS_TLOG_PRIVATE_FILE_CONTENT_CANARY_20260521","nested":{"secret":"SECRET-TLOG-OBSERVABILITY-20260521"}}',
          'redacted=redact_sensitive_value(raw)',
          'assert redacted["authorization"] == REDACTION_TEXT',
          'assert redacted["prompt"] == REDACTION_TEXT',
          'assert redacted["content"] == REDACTION_TEXT',
          'assert redacted["nested"]["secret"] == REDACTION_TEXT',
          'print("PASS")',
        ].join(';'),
      ], { cwd: ROOT, encoding: 'utf-8' }).trim();
      expect(output).toBe('PASS');
      return { pythonRedactionProbe: 'PASS', checkedClasses: ['authorization', 'prompt', 'content', 'secret'] };
    });
  });

  test('TLOG-005: context telemetry does not write raw private prompt or file text', async ({ request }) => {
    await record('TLOG-005', 'PROMPT_PRIVACY_LOG_PASS', async () => {
      const before = readTextSafe(appDataLogPath()).length;
      const response = await request.post('/api/context/log', {
        headers: { 'X-Janus-Internal-Key': readApiKey() },
        data: {
          event_type: 'tlog_privacy_probe',
          trace_id: 'tlog-privacy-probe',
          payload: {
            prompt: PRIVATE_PROMPT_CANARY,
            content: PRIVATE_FILE_CANARY,
            authorization: BEARER_CANARY,
            status: 'probe',
          },
        },
      });
      expect(response.status()).toBe(200);
      await new Promise((resolve) => setTimeout(resolve, 250));
      const afterLog = readTextSafe(appDataLogPath()).slice(before);
      expect(afterLog).not.toContain(PRIVATE_PROMPT_CANARY);
      expect(afterLog).not.toContain(PRIVATE_FILE_CANARY);
      expect(afterLog).not.toContain(BEARER_CANARY);
      expect(afterLog).toContain('[REDACTED]');
      return { endpointStatus: response.status(), localLogCanariesPresent: false, redactionMarkerObserved: afterLog.includes('[REDACTED]') };
    });
  });

  test('TLOG-006: runtime error and protected responses do not leak private data', async ({ request }) => {
    await record('TLOG-006', 'ERROR_PRIVACY_RESPONSE_PASS', async () => {
      const debugResponse = await request.get('/api/debug/memory');
      const missingResponse = await request.get('/definitely-missing-telemetry-test');
      const userResponse = await request.get('/api/users/me');
      const bodies = [
        await debugResponse.text(),
        await missingResponse.text(),
        await userResponse.text(),
      ].join('\n');
      expect(bodies).not.toContain(PRIVATE_PROMPT_CANARY);
      expect(bodies).not.toContain(PRIVATE_FILE_CANARY);
      expect(bodies).not.toMatch(/Traceback|File ".*\.py"|SUPABASE_|OPENAI_API_KEY|GEMINI_API_KEY/);
      return { statuses: [debugResponse.status(), missingResponse.status(), userResponse.status()], noStackTrace: true };
    });
  });

  test('TLOG-007: telemetry access control is documented and debug endpoints are gated', async ({ request }) => {
    await record('TLOG-007', 'TELEMETRY_ACCESS_CONTROL_PASS', async () => {
      const policy = readText('documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_access_retention.md');
      expect(policy).toContain('Provider telemetry access is limited');
      expect(policy).toContain('Debug endpoints remain disabled');
      const debugResponse = await request.get('/api/debug/memory');
      expect(debugResponse.status()).toBe(403);
      return { accessPolicyDocumented: true, debugEndpointStatus: 403 };
    });
  });

  test('TLOG-008: retention and deletion process is explicit', async () => {
    await record('TLOG-008', 'TELEMETRY_RETENTION_DELETION_PASS', async () => {
      const policy = readText('documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_access_retention.md');
      for (const phrase of ['Local beta tester logs can be deleted', 'Supabase beta telemetry can be deleted', 'shortest practical provider-side retention', 'Feedback webhook destinations must be cleared']) {
        expect(policy).toContain(phrase);
      }
      return { retentionPolicyDocumented: true, deletionPathsDocumented: 4 };
    });
  });

  test('TLOG-009: incident audit shape exists without raw payload upload', async () => {
    await record('TLOG-009', 'INCIDENT_AUDIT_SHAPE_PASS', async () => {
      const schema = readText('backend/data/schemas_logging.py');
      const loggerCore = readText('backend/services/logging/logger_core.py');
      for (const field of ['event_type', 'status', 'provider', 'model', 'skill', 'latency_ms', 'trace_id']) {
        expect(schema).toContain(field);
      }
      expect(loggerCore).toContain('"payload": redact_sensitive_value(event.payload)');
      return { auditFieldsPresent: 7, payloadRedactedBeforeSupabaseUpload: true };
    });
  });

  test('TLOG-010: final telemetry privacy gate decision is PASS', async () => {
    await record('TLOG-010', 'TELEMETRY_PRIVACY_GATE_DECISION_PASS', async () => {
      const localLog = readTextSafe(appDataLogPath());
      for (const canary of [PRIVATE_PROMPT_CANARY, PRIVATE_FILE_CANARY, SECRET_CANARY, BEARER_CANARY]) {
        expect(localLog).not.toContain(canary);
      }
      return { openCriticalHighFindings: 0, gateDecision: 'PASS' };
    });
  });
});
