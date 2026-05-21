/**
 * TEST-RUN-2026-05-21-005 Staging Environment Security Baseline
 *
 * This runner intentionally does not start local Janus services. It validates
 * a real staging target only when explicit JANUS_STAGING_* variables are set.
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const TEST_RUN_ID = 'TEST-RUN-2026-05-21-005';
const TITLE = 'Janus Staging Environment Security Baseline';
const ROOT = process.cwd();
const RESULT_DIR = path.join(ROOT, 'documentation', 'test-results', TEST_RUN_ID);
const RESULT_JSON = path.join(ROOT, 'documentation', 'test-results', `${TEST_RUN_ID}_results.json`);
const SPEC_PATH = 'documentation/TEST_SPEC/02_security_safety/11_staging_environment_security_baseline.md';

const results = [];

function rel(filePath) {
  return path.relative(ROOT, filePath).replaceAll(path.sep, '/');
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function env(name) {
  const value = process.env[name];
  return typeof value === 'string' ? value.trim() : '';
}

function redactPresence(value) {
  if (!value) return 'missing';
  return `present(length=${value.length})`;
}

function isLocalUrl(value) {
  if (!value) return false;
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    return (
      ['localhost', '127.0.0.1', '::1', '0.0.0.0'].includes(host) ||
      url.protocol === 'file:' ||
      url.protocol === 'janus:'
    );
  } catch {
    return true;
  }
}

function requireStagingUrl(name) {
  const value = env(name);
  if (!value) {
    return { blocked: true, reason: `${name} is not configured.` };
  }
  if (isLocalUrl(value)) {
    return { blocked: true, reason: `${name} points to a local/dev URL and cannot prove staging.`, value };
  }
  return { blocked: false, value };
}

function requireEnv(name, validator = () => true, validationReason = 'value did not satisfy staging policy') {
  const value = env(name);
  if (!value) return { blocked: true, reason: `${name} is not configured.` };
  if (!validator(value)) return { blocked: true, reason: `${name}: ${validationReason}`, value };
  return { blocked: false, value };
}

async function runCase(testCaseId, body) {
  const started = Date.now();
  const evidencePath = path.join(RESULT_DIR, `${testCaseId}_evidence.json`);
  try {
    const evidence = await body();
    const result = evidence.result || 'PASS';
    const payload = {
      testRunId: TEST_RUN_ID,
      testCaseId,
      result,
      classification: evidence.classification || (result === 'BLOCKED' ? 'STAGING_GATE_BLOCKED' : 'STAGING_GATE_PASS'),
      evidence: evidence.evidence || evidence,
      timestamp: new Date().toISOString(),
    };
    fs.writeFileSync(evidencePath, JSON.stringify(payload, null, 2));
    results.push({
      testCaseId,
      result,
      classification: payload.classification,
      evidencePath: rel(evidencePath),
      durationMs: Date.now() - started,
      notes: evidence.notes || '',
      timestamp: payload.timestamp,
    });
  } catch (error) {
    const payload = {
      testRunId: TEST_RUN_ID,
      testCaseId,
      result: 'FAIL',
      classification: 'STAGING_GATE_ASSERTION_FAIL',
      error: String(error && error.stack ? error.stack : error),
      timestamp: new Date().toISOString(),
    };
    fs.writeFileSync(evidencePath, JSON.stringify(payload, null, 2));
    results.push({
      testCaseId,
      result: 'FAIL',
      classification: payload.classification,
      evidencePath: rel(evidencePath),
      durationMs: Date.now() - started,
      notes: payload.error.slice(0, 500),
      timestamp: payload.timestamp,
    });
    throw error;
  }
}

function blocked(reason, evidence = {}) {
  return {
    result: 'BLOCKED',
    classification: 'STAGING_ENVIRONMENT_NOT_CONFIGURED',
    notes: reason,
    evidence: { blocker: reason, ...evidence },
  };
}

test.describe.serial(`${TEST_RUN_ID}: ${TITLE}`, () => {
  test.beforeAll(() => {
    ensureDir(RESULT_DIR);
  });

  test.afterAll(() => {
    const failed = results.filter((item) => item.result === 'FAIL').length;
    const blockedCount = results.filter((item) => item.result === 'BLOCKED').length;
    const summary = {
      total: results.length,
      passed: results.filter((item) => item.result === 'PASS').length,
      failed,
      blocked: blockedCount,
      manualGateRequired: blockedCount > 0 ? 1 : 0,
    };
    const status = failed > 0 ? 'FAIL' : blockedCount > 0 ? 'BLOCKED' : 'PASS';
    const result = {
      schemaVersion: 'janus.test-result.v1',
      testRunId: TEST_RUN_ID,
      title: TITLE,
      status,
      summary,
      artifacts: {
        resultDirectory: rel(RESULT_DIR),
        resultJson: rel(RESULT_JSON),
        evidenceFiles: results.map((item) => item.evidencePath),
      },
      results,
      updatedAt: new Date().toISOString(),
    };
    fs.writeFileSync(RESULT_JSON, JSON.stringify(result, null, 2));
  });

  test('STG-001: staging frontend and health URL are reachable', async ({ request }) => {
    await runCase('STG-001', async () => {
      const frontend = requireStagingUrl('JANUS_STAGING_FRONTEND_URL');
      const health = requireStagingUrl('JANUS_STAGING_HEALTH_URL');
      if (frontend.blocked || health.blocked) {
        return blocked('Explicit non-local JANUS_STAGING_FRONTEND_URL and JANUS_STAGING_HEALTH_URL are required.', {
          frontend,
          health,
        });
      }
      const frontendResponse = await request.get(frontend.value, { timeout: 15000 });
      const healthResponse = await request.get(health.value, { timeout: 15000 });
      expect(frontendResponse.ok()).toBeTruthy();
      expect(healthResponse.ok()).toBeTruthy();
      return {
        classification: 'STAGING_REACHABILITY_PASS',
        evidence: {
          frontendUrl: frontend.value,
          healthUrl: health.value,
          frontendStatus: frontendResponse.status(),
          healthStatus: healthResponse.status(),
        },
      };
    });
  });

  test('STG-002: environment identity is staging/beta, not dev or production', async ({ request }) => {
    await runCase('STG-002', async () => {
      const metadataUrl = requireStagingUrl('JANUS_STAGING_METADATA_URL');
      const declared = requireEnv(
        'JANUS_STAGING_ENVIRONMENT_NAME',
        (value) => /^(staging|beta|preprod|pre-production)$/i.test(value),
        'must be staging, beta, preprod, or pre-production'
      );
      if (metadataUrl.blocked || declared.blocked) {
        return blocked('Staging metadata URL and explicit environment name are required.', {
          metadataUrl,
          declared,
        });
      }
      const response = await request.get(metadataUrl.value, { timeout: 15000 });
      expect(response.ok()).toBeTruthy();
      return {
        classification: 'STAGING_IDENTITY_PASS',
        evidence: {
          metadataUrl: metadataUrl.value,
          environmentName: declared.value,
          metadataStatus: response.status(),
        },
      };
    });
  });

  test('STG-003: database and storage are isolated from production', async () => {
    await runCase('STG-003', async () => {
      const stagingStore = requireEnv('JANUS_STAGING_DATASTORE_ID');
      const productionStore = requireEnv('JANUS_PRODUCTION_DATASTORE_ID');
      if (stagingStore.blocked || productionStore.blocked) {
        return blocked('Redacted staging and production datastore identifiers are required to prove isolation.', {
          stagingStore: { ...stagingStore, value: redactPresence(stagingStore.value || '') },
          productionStore: { ...productionStore, value: redactPresence(productionStore.value || '') },
        });
      }
      expect(stagingStore.value).not.toBe(productionStore.value);
      expect(stagingStore.value.toLowerCase()).not.toContain('prod');
      return {
        classification: 'STAGING_DATA_ISOLATION_PASS',
        evidence: {
          stagingDatastore: redactPresence(stagingStore.value),
          productionDatastore: redactPresence(productionStore.value),
          equal: false,
        },
      };
    });
  });

  test('STG-004: secrets come from an approved deployment secret source', async () => {
    await runCase('STG-004', async () => {
      const source = requireEnv(
        'JANUS_STAGING_SECRET_SOURCE',
        (value) => !/(^|[\\/])\.env$|repo|local|appdata|developer/i.test(value),
        'must not be repo, local .env, AppData, or developer-local config'
      );
      if (source.blocked) {
        return blocked('Approved staging secret source is required.', { source });
      }
      return {
        classification: 'STAGING_SECRET_SOURCE_PASS',
        evidence: { secretSource: source.value, rawSecretsWrittenToEvidence: false },
      };
    });
  });

  test('STG-005: debug mode and stack traces are disabled or protected', async ({ request }) => {
    await runCase('STG-005', async () => {
      const base = requireStagingUrl('JANUS_STAGING_BACKEND_URL');
      if (base.blocked) return blocked('JANUS_STAGING_BACKEND_URL is required for debug-route probing.', { base });
      const candidates = ['/debug', '/api/debug', '/api/docs', '/openapi.json'];
      const responses = [];
      for (const suffix of candidates) {
        const url = new URL(suffix, base.value).toString();
        const response = await request.get(url, { timeout: 10000, failOnStatusCode: false });
        responses.push({ path: suffix, status: response.status() });
        expect([401, 403, 404]).toContain(response.status());
      }
      return { classification: 'STAGING_DEBUG_SURFACE_PASS', evidence: { baseUrl: base.value, responses } };
    });
  });

  test('STG-006: build artifact is beta/staging-safe', async () => {
    await runCase('STG-006', async () => {
      const build = requireEnv('JANUS_STAGING_BUILD_VERSION');
      const sourcemapPolicy = requireEnv(
        'JANUS_STAGING_SOURCEMAP_POLICY',
        (value) => /^(disabled|private|authenticated)$/i.test(value),
        'must be disabled, private, or authenticated'
      );
      if (build.blocked || sourcemapPolicy.blocked) {
        return blocked('Build version and sourcemap policy are required.', { build, sourcemapPolicy });
      }
      return {
        classification: 'STAGING_BUILD_ARTIFACT_PASS',
        evidence: { buildVersion: build.value, sourcemapPolicy: sourcemapPolicy.value },
      };
    });
  });

  test('STG-007: provider mode is staging/beta scoped and cost capped', async () => {
    await runCase('STG-007', async () => {
      const mode = requireEnv(
        'JANUS_STAGING_PROVIDER_MODE',
        (value) => /^(staging|beta|capped|sandbox|local-only)$/i.test(value),
        'must identify a staging/beta/capped/sandbox/local-only provider mode'
      );
      const cap = requireEnv('JANUS_STAGING_PROVIDER_COST_CAP');
      if (mode.blocked || cap.blocked) {
        return blocked('Provider mode and cost cap are required.', { mode, cap });
      }
      return {
        classification: 'STAGING_PROVIDER_MODE_PASS',
        evidence: { providerMode: mode.value, providerCostCap: cap.value },
      };
    });
  });

  test('STG-008: deployment provenance and rollback target are documented', async () => {
    await runCase('STG-008', async () => {
      const commit = requireEnv('JANUS_STAGING_DEPLOY_COMMIT');
      const rollback = requireEnv('JANUS_STAGING_ROLLBACK_TARGET');
      if (commit.blocked || rollback.blocked) {
        return blocked('Deployment commit and rollback target are required.', { commit, rollback });
      }
      return {
        classification: 'STAGING_DEPLOY_PROVENANCE_PASS',
        evidence: { deployCommit: commit.value, rollbackTarget: rollback.value },
      };
    });
  });

  test('STG-009: generated evidence contains no raw secret patterns', async () => {
    await runCase('STG-009', async () => {
      const scanTargets = fs.existsSync(RESULT_DIR)
        ? fs.readdirSync(RESULT_DIR).filter((name) => name.endsWith('_evidence.json'))
        : [];
      const strictSecretPattern = /(sk-[A-Za-z0-9_-]{12,}|AIza[0-9A-Za-z_-]{20,}|Bearer\s+[A-Za-z0-9._~+/=-]{8,}|password\s*[:=]|secret\s*[:=]|api[_-]?key\s*[:=])/i;
      const findings = [];
      for (const name of scanTargets) {
        const text = fs.readFileSync(path.join(RESULT_DIR, name), 'utf-8');
        if (strictSecretPattern.test(text)) findings.push(name);
      }
      expect(findings).toEqual([]);
      return {
        classification: 'STAGING_EVIDENCE_HYGIENE_PASS',
        evidence: { scannedEvidenceFiles: scanTargets.length, findings },
      };
    });
  });

  test('STG-010: staging gate decision is explicit', async () => {
    await runCase('STG-010', async () => {
      const required = [
        'JANUS_STAGING_FRONTEND_URL',
        'JANUS_STAGING_HEALTH_URL',
        'JANUS_STAGING_ENVIRONMENT_NAME',
        'JANUS_STAGING_DATASTORE_ID',
        'JANUS_PRODUCTION_DATASTORE_ID',
        'JANUS_STAGING_SECRET_SOURCE',
        'JANUS_STAGING_BACKEND_URL',
        'JANUS_STAGING_BUILD_VERSION',
        'JANUS_STAGING_PROVIDER_MODE',
        'JANUS_STAGING_PROVIDER_COST_CAP',
        'JANUS_STAGING_DEPLOY_COMMIT',
        'JANUS_STAGING_ROLLBACK_TARGET',
      ];
      const missing = required.filter((name) => !env(name));
      if (missing.length > 0) {
        return blocked('Staging gate is BLOCKED until explicit non-local staging configuration is provided.', {
          missing,
          decision: 'BLOCKED',
        });
      }
      return {
        classification: 'STAGING_GATE_DECISION_PASS',
        evidence: { decision: 'PASS', missing: [] },
      };
    });
  });
});
