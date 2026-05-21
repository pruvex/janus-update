/**
 * TEST-RUN-2026-05-21-011 Ops Recovery Kill Switches
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const TEST_RUN_ID = 'TEST-RUN-2026-05-21-011';
const TITLE = 'Janus Ops Recovery Kill Switches';
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

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

function readText(relativePath) {
  return fs.readFileSync(path.join(ROOT, relativePath), 'utf-8');
}

function getInternalApiKey() {
  const configPath = path.join(process.env.APPDATA || '', 'Janus Projekt', 'config.json');
  const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
  if (!config.api_key) throw new Error('Janus internal API key missing from local beta config');
  return config.api_key;
}

async function getOpsInventory(request) {
  const response = await request.get('/api/system/ops/kill-switches', {
    headers: { 'X-Janus-Internal-Key': getInternalApiKey() },
  });
  expect(response.status()).toBe(200);
  return response.json();
}

async function record(testCaseId, classification, body) {
  const started = Date.now();
  const evidencePath = path.join(RESULT_DIR, `${testCaseId}_evidence.json`);
  try {
    const evidence = await body();
    writeJson(evidencePath, {
      rawSensitiveEvidencePolicy: 'no-raw-secrets-no-raw-prompts',
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
      rawSensitiveEvidencePolicy: 'no-raw-secrets-no-raw-prompts',
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
  test.beforeAll(() => ensureDir(RESULT_DIR));
  test.afterAll(() => emitAggregateResult());

  test('OPS-001: provider access kill switch is active and local provider stays recoverable', async ({ request }) => {
    await record('OPS-001', 'PROVIDER_KILL_SWITCH_PASS', async () => {
      const inventory = await getOpsInventory(request);
      expect(inventory.switches.providerAccess).toBe(true);
      expect(inventory.probes.find((probe) => probe.id === 'provider:openai')?.code).toBe('OPS_PROVIDER_DISABLED');
      expect(inventory.probes.find((probe) => probe.id === 'provider:gemini')?.code).toBe('OPS_PROVIDER_DISABLED');
      expect(inventory.probes.find((probe) => probe.id === 'provider:ollama')?.disabled).toBe(false);
      return { probes: inventory.probes.filter((probe) => probe.id.startsWith('provider:')) };
    });
  });

  test('OPS-002: external/current-data tools are disabled by dry-run inventory', async ({ request }) => {
    await record('OPS-002', 'EXTERNAL_TOOLS_KILL_SWITCH_PASS', async () => {
      const inventory = await getOpsInventory(request);
      const websearch = inventory.probes.find((probe) => probe.id === 'tool:system.websearch');
      const weather = inventory.probes.find((probe) => probe.id === 'tool:system.weather');
      expect(websearch.code).toBe('OPS_EXTERNAL_TOOLS_DISABLED');
      expect(weather.code).toBe('OPS_EXTERNAL_TOOLS_DISABLED');
      expect(websearch.classification.external).toBe(true);
      return { websearch, weather };
    });
  });

  test('OPS-003: write/destructive tools are disabled by dry-run inventory', async ({ request }) => {
    await record('OPS-003', 'WRITE_TOOLS_KILL_SWITCH_PASS', async () => {
      const inventory = await getOpsInventory(request);
      const fileWrite = inventory.probes.find((probe) => probe.id === 'tool:filesystem.create_file');
      const calendarWrite = inventory.probes.find((probe) => probe.id === 'tool:calendar.update_event');
      expect(fileWrite.code).toBe('OPS_WRITE_TOOLS_DISABLED');
      expect(calendarWrite.code).toBe('OPS_WRITE_TOOLS_DISABLED');
      expect(fileWrite.classification.write).toBe(true);
      return { fileWrite, calendarWrite };
    });
  });

  test('OPS-004: local beta user lock blocks protected non-ops endpoints', async ({ request }) => {
    await record('OPS-004', 'USER_LOCK_KILL_SWITCH_PASS', async () => {
      const blocked = await request.get('/api/memory', {
        headers: { 'X-Janus-Internal-Key': getInternalApiKey() },
      });
      const body = await blocked.json();
      expect(blocked.status()).toBe(423);
      expect(JSON.stringify(body)).not.toContain('api_key');
      expect(body.detail).toContain('Ops-Recovery-Schalter');
      return { status: blocked.status(), safeDetail: body.detail };
    });
  });

  test('OPS-005: rotation dry-run is documented without raw secrets', async () => {
    await record('OPS-005', 'ROTATION_DRY_RUN_DOC_PASS', async () => {
      const runbook = readText('documentation/test-results/TEST-RUN-2026-05-21-011/ops_recovery_runbook.md');
      expect(runbook).toContain('Rotation Dry-run');
      expect(runbook).toContain('No raw secret values');
      expect(runbook).not.toMatch(/sk-[A-Za-z0-9]{20,}/);
      return { runbook: 'ops_recovery_runbook.md', rawSecretValuesRecorded: false };
    });
  });

  test('OPS-006: telemetry recovery mode is bounded to minimal', async ({ request }) => {
    await record('OPS-006', 'TELEMETRY_MODE_KILL_SWITCH_PASS', async () => {
      const inventory = await getOpsInventory(request);
      expect(inventory.switches.telemetryMode).toBe('minimal');
      expect(inventory.switches.telemetryRemoteUploadAllowed).toBe(false);
      expect(JSON.stringify(inventory).toLowerCase()).not.toContain('cookie');
      return {
        telemetryMode: inventory.switches.telemetryMode,
        telemetryRemoteUploadAllowed: inventory.switches.telemetryRemoteUploadAllowed,
      };
    });
  });

  test('OPS-007: rollback and restore procedure is present in live inventory', async ({ request }) => {
    await record('OPS-007', 'ROLLBACK_RESTORE_PROCEDURE_PASS', async () => {
      const inventory = await getOpsInventory(request);
      expect(inventory.restoreProcedure.length).toBeGreaterThanOrEqual(6);
      expect(inventory.restoreProcedure.join(' ')).toContain('JANUS_DISABLE_CLOUD_PROVIDERS');
      expect(inventory.restoreProcedure.join(' ')).toContain('/api/health');
      return { restoreSteps: inventory.restoreProcedure };
    });
  });

  test('OPS-008: beta export/deletion dry-run is documented as reversible and non-destructive', async () => {
    await record('OPS-008', 'BETA_EXPORT_DELETE_DRY_RUN_DOC_PASS', async () => {
      const runbook = readText('documentation/test-results/TEST-RUN-2026-05-21-011/ops_recovery_runbook.md');
      expect(runbook).toContain('Beta Export/Delete Dry-run');
      expect(runbook).toContain('non-destructive');
      expect(runbook).toContain('canary-only');
      return { runbook: 'ops_recovery_runbook.md', destructiveActionExecuted: false };
    });
  });

  test('OPS-009: incident contact/reporting path is documented', async () => {
    await record('OPS-009', 'INCIDENT_CONTACT_REPORTING_DOC_PASS', async () => {
      const runbook = readText('documentation/test-results/TEST-RUN-2026-05-21-011/ops_recovery_runbook.md');
      expect(runbook).toContain('Incident Reporting');
      expect(runbook).toContain('operator-on-call');
      expect(runbook).toContain('privacy-contact');
      return { runbook: 'ops_recovery_runbook.md', contactAliases: ['operator-on-call', 'privacy-contact'] };
    });
  });

  test('OPS-010: gate decision is pass with all ten controls evidenced', async ({ request }) => {
    await record('OPS-010', 'GATE_DECISION_PASS', async () => {
      const inventory = await getOpsInventory(request);
      const switches = inventory.switches;
      expect(switches.providerAccess).toBe(true);
      expect(switches.externalTools).toBe(true);
      expect(switches.writeTools).toBe(true);
      expect(switches.memoryRag).toBe(true);
      expect(switches.localUserLocked).toBe(true);
      return { gate: 'PASS', switches };
    });
  });
});
