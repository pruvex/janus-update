/**
 * TEST-RUN-2026-05-21-013 Final Beta Launch Gate Review
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const TEST_RUN_ID = 'TEST-RUN-2026-05-21-013';
const TITLE = 'Janus Final Beta Launch Gate Review';
const ROOT = process.cwd();
const RESULT_DIR = path.join(ROOT, 'documentation', 'test-results', TEST_RUN_ID);
const RESULT_JSON = path.join(ROOT, 'documentation', 'test-results', `${TEST_RUN_ID}_results.json`);
const RESULT_MD = path.join(ROOT, 'documentation', 'test-results', `${TEST_RUN_ID}_results.md`);
const results = [];

const securityRuns = [
  ['01', 'TEST-RUN-2026-05-17-021', 28],
  ['02', 'TEST-RUN-2026-05-17-028', 26],
  ['03', 'TEST-RUN-2026-05-18-019', 26],
  ['04', 'TEST-RUN-2026-05-18-024', 13],
  ['05', 'TEST-RUN-2026-05-18-027', 26],
  ['06', 'TEST-RUN-2026-05-20-012', 57],
  ['07', 'TEST-RUN-2026-05-20-018', 26],
  ['08', 'TEST-RUN-2026-05-20-023', 28],
  ['09', 'TEST-RUN-2026-05-21-003', 10],
  ['10', 'TEST-RUN-2026-05-21-004', 12],
  ['11', 'TEST-RUN-2026-05-21-005', 10],
  ['12', 'TEST-RUN-2026-05-21-006', 10],
  ['13', 'TEST-RUN-2026-05-21-007', 10],
  ['14', 'TEST-RUN-2026-05-21-008', 10],
  ['15', 'TEST-RUN-2026-05-21-009', 10],
  ['16', 'TEST-RUN-2026-05-21-010', 10],
  ['17', 'TEST-RUN-2026-05-21-011', 10],
  ['18', 'TEST-RUN-2026-05-21-012', 10],
];

function rel(filePath) {
  return path.relative(ROOT, filePath).replaceAll(path.sep, '/');
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readText(relativePath) {
  return fs.readFileSync(path.join(ROOT, relativePath), 'utf-8');
}

function readJson(relativePath) {
  return JSON.parse(readText(relativePath));
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

function required(pathName) {
  const absolute = path.join(ROOT, pathName);
  expect(fs.existsSync(absolute), `${pathName} must exist`).toBeTruthy();
  expect(fs.statSync(absolute).size, `${pathName} must be nonempty`).toBeGreaterThan(200);
  return pathName;
}

async function record(testCaseId, classification, body) {
  const started = Date.now();
  const evidencePath = path.join(RESULT_DIR, `${testCaseId}_evidence.json`);
  try {
    const evidence = await body();
    writeJson(evidencePath, {
      rawSensitiveEvidencePolicy: 'no-raw-secrets-no-raw-private-data-no-tester-payloads',
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
      rawSensitiveEvidencePolicy: 'no-raw-secrets-no-raw-private-data-no-tester-payloads',
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
  const status = failed === 0 && blocked === 0 && passed === 12 ? 'PASS' : failed > 0 ? 'FAIL' : 'PARTIAL';
  const aggregate = {
    schemaVersion: 'janus.test-result.v1',
    testRunId: TEST_RUN_ID,
    title: TITLE,
    status,
    decision: 'PASS WITH WATCHPOINTS',
    summary: { total: 12, passed, failed, blocked, manualGateRequired: 0 },
    artifacts: {
      resultDirectory: rel(RESULT_DIR),
      resultJson: rel(RESULT_JSON),
      resultMarkdown: rel(RESULT_MD),
      evidenceFiles: results.map((item) => item.evidencePath),
      finalAudit: `documentation/test-runs/${TEST_RUN_ID}_final_audit.md`,
      riskRegister: `documentation/test-runs/${TEST_RUN_ID}_final_risk_register.md`,
      signoff: `documentation/test-runs/${TEST_RUN_ID}_owner_signoff.md`,
      matrix: `documentation/test-runs/${TEST_RUN_ID}_security_01_18_matrix.md`,
    },
    results,
    updatedAt: new Date().toISOString(),
  };
  writeJson(RESULT_JSON, aggregate);
  fs.writeFileSync(
    RESULT_MD,
    [
      `# ${TEST_RUN_ID} Results`,
      '',
      `Status: ${status}`,
      'Decision: PASS WITH WATCHPOINTS',
      '',
      `Summary: ${passed}/12 passed, ${failed} failed, ${blocked} blocked.`,
      '',
      '| Test | Result | Classification | Evidence |',
      '|---|---|---|---|',
      ...results.map((item) => `| ${item.testCaseId} | ${item.result} | ${item.classification} | \`${item.evidencePath}\` |`),
      '',
    ].join('\n'),
  );
}

function assertResult(runId, expectedTotal) {
  const result = readJson(`documentation/test-results/${runId}_results.json`);
  expect(result.status).toBe('PASS');
  expect(result.summary.total).toBe(expectedTotal);
  expect(result.summary.passed).toBe(expectedTotal);
  expect(result.summary.failed).toBe(0);
  expect(result.summary.blocked).toBe(0);
  return {
    runId,
    status: result.status,
    total: result.summary.total,
    passed: result.summary.passed,
    failed: result.summary.failed,
    blocked: result.summary.blocked,
  };
}

test.describe(`${TEST_RUN_ID}: ${TITLE}`, () => {
  test.beforeAll(() => ensureDir(RESULT_DIR));
  test.afterAll(() => emitAggregateResult());

  test('BLG-001: baseline Security 01-10 results are fully PASS', async () => {
    await record('BLG-001', 'BASELINE_SECURITY_01_10_PASS', async () => {
      const checked = securityRuns.slice(0, 10).map(([, runId, total]) => assertResult(runId, total));
      return { checkedRuns: checked, failed: 0, blocked: 0 };
    });
  });

  test('BLG-002: Security 11 environment baseline evidence is complete', async () => {
    await record('BLG-002', 'STAGING_ENVIRONMENT_EVIDENCE_PASS', async () => ({
      result: assertResult('TEST-RUN-2026-05-21-005', 10),
      artifacts: [
        required('documentation/test-runs/TEST-RUN-2026-05-21-005_final_audit.md'),
        required('documentation/test-runs/TEST-RUN-2026-05-21-005_staging_environment_map.md'),
      ],
    }));
  });

  test('BLG-003: Security 12 profile isolation evidence is complete', async () => {
    await record('BLG-003', 'MULTI_ACCOUNT_ISOLATION_EVIDENCE_PASS', async () => ({
      result: assertResult('TEST-RUN-2026-05-21-006', 10),
      artifacts: [
        required('documentation/test-runs/TEST-RUN-2026-05-21-006_final_audit.md'),
        required('documentation/test-runs/TEST-RUN-2026-05-21-006_profile_isolation_map.md'),
      ],
    }));
  });

  test('BLG-004: Security 13 secret rotation and leak scan evidence is complete', async () => {
    await record('BLG-004', 'SECRET_ROTATION_LEAK_SCAN_EVIDENCE_PASS', async () => ({
      result: assertResult('TEST-RUN-2026-05-21-007', 10),
      artifacts: [
        required('documentation/test-runs/TEST-RUN-2026-05-21-007_final_audit.md'),
        required('documentation/test-runs/TEST-RUN-2026-05-21-007_secret_inventory.md'),
        required('documentation/test-runs/TEST-RUN-2026-05-21-007_secret_rotation_runbook.md'),
      ],
    }));
  });

  test('BLG-005: Security 14 telemetry privacy evidence is complete', async () => {
    await record('BLG-005', 'TELEMETRY_PRIVACY_EVIDENCE_PASS', async () => ({
      result: assertResult('TEST-RUN-2026-05-21-008', 10),
      artifacts: [
        required('documentation/test-runs/TEST-RUN-2026-05-21-008_final_audit.md'),
        required('documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_sink_inventory.md'),
        required('documentation/test-runs/TEST-RUN-2026-05-21-008_telemetry_access_retention.md'),
      ],
    }));
  });

  test('BLG-006: Security 15 deployment surface evidence is complete', async () => {
    await record('BLG-006', 'DEPLOYMENT_SURFACE_EVIDENCE_PASS', async () => ({
      result: assertResult('TEST-RUN-2026-05-21-009', 10),
      artifacts: [
        required('documentation/test-runs/TEST-RUN-2026-05-21-009_final_audit.md'),
        required('documentation/test-runs/TEST-RUN-2026-05-21-009_deployment_surface_policy.md'),
      ],
    }));
  });

  test('BLG-007: Security 16 abuse and cost-control evidence is complete', async () => {
    await record('BLG-007', 'ABUSE_COST_CONTROL_EVIDENCE_PASS', async () => ({
      result: assertResult('TEST-RUN-2026-05-21-010', 10),
      artifacts: [
        required('documentation/test-runs/TEST-RUN-2026-05-21-010_final_audit.md'),
        required('documentation/test-runs/TEST-RUN-2026-05-21-010_beta_abuse_limit_policy.md'),
      ],
    }));
  });

  test('BLG-008: Security 17 ops recovery evidence is complete', async () => {
    await record('BLG-008', 'OPS_RECOVERY_EVIDENCE_PASS', async () => ({
      result: assertResult('TEST-RUN-2026-05-21-011', 10),
      artifacts: [
        required('documentation/test-runs/TEST-RUN-2026-05-21-011_final_audit.md'),
        required('documentation/test-results/TEST-RUN-2026-05-21-011/ops_recovery_runbook.md'),
      ],
    }));
  });

  test('BLG-009: Security 18 privacy notice evidence is complete', async () => {
    await record('BLG-009', 'PRIVACY_NOTICE_EVIDENCE_PASS', async () => ({
      result: assertResult('TEST-RUN-2026-05-21-012', 10),
      artifacts: [
        required('documentation/test-runs/TEST-RUN-2026-05-21-012_final_audit.md'),
        required('documentation/beta/BETA_PRIVACY_NOTICE.md'),
        required('documentation/beta/BETA_DATA_RIGHTS_PROCESS.md'),
        required('documentation/beta/BETA_TESTER_ONBOARDING_PRIVACY_ACK.md'),
      ],
    }));
  });

  test('BLG-010: final risk register has no open Critical or High findings', async () => {
    await record('BLG-010', 'FINAL_RISK_REGISTER_PASS', async () => {
      const risk = readText(`documentation/test-runs/${TEST_RUN_ID}_final_risk_register.md`).toLowerCase();
      expect(risk).toContain('no open critical');
      expect(risk).toContain('no open high');
      expect(risk).not.toContain('| critical | open |');
      expect(risk).not.toContain('| high | open |');
      expect(risk).toContain('accepted/tracked');
      return { openCritical: 0, openHigh: 0, watchpointsAcceptedAndTracked: true };
    });
  });

  test('BLG-011: owner sign-off records accountability and scope', async () => {
    await record('BLG-011', 'OWNER_SIGNOFF_PASS', async () => {
      const signoff = readText(`documentation/test-runs/${TEST_RUN_ID}_owner_signoff.md`).toLowerCase();
      for (const term of ['pass with watchpoints', 'janus-release-owner', 'security-review-owner', 'operator-on-call', 'privacy-contact']) {
        expect(signoff).toContain(term);
      }
      expect(signoff).toContain('hosted saas');
      expect(signoff).toContain('not certified by this gate');
      return { owners: ['janus-release-owner', 'security-review-owner', 'operator-on-call', 'privacy-contact'], scope: 'packaged-local beta' };
    });
  });

  test('BLG-012: final decision is evidence-backed and honest about limits', async () => {
    await record('BLG-012', 'FINAL_DECISION_PASS_WITH_WATCHPOINTS', async () => {
      const audit = readText(`documentation/test-runs/${TEST_RUN_ID}_final_audit.md`).toLowerCase();
      const matrix = readText(`documentation/test-runs/${TEST_RUN_ID}_security_01_18_matrix.md`).toLowerCase();
      for (const term of ['pass with watchpoints', 'controlled external packaged-local beta may begin', 'not a public/commercial production release approval']) {
        expect(audit).toContain(term);
      }
      expect(matrix).toContain('failed checks across latest listed runs: 0');
      expect(matrix).toContain('blocked checks across latest listed runs: 0');
      return { decision: 'PASS WITH WATCHPOINTS', dashboardStatus: 'PASS', publicProductionApproval: false };
    });
  });
});
