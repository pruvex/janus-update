/**
 * TEST-RUN-2026-05-21-004 Security ReviewSpec Suite Runner
 *
 * This runner validates the post-test security review evidence chain.
 * It is intentionally static/meta-review focused: the underlying live
 * security behavior is covered by Security TestSpecs 01-09 and linked here.
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const TEST_RUN_ID = 'TEST-RUN-2026-05-21-004';
const TITLE = 'Janus Security ReviewSpec Suite';
const ROOT = process.cwd();
const RESULT_DIR = path.join(ROOT, 'documentation', 'test-results', TEST_RUN_ID);
const RESULT_JSON = path.join(ROOT, 'documentation', 'test-results', `${TEST_RUN_ID}_results.json`);
const SPEC_PATH = path.join(ROOT, 'documentation', 'TEST_SPEC', '02_security_safety', '10_security_reviewspec_suite.md');

const SECURITY_BASELINE = [
  ['01', 'TEST-RUN-2026-05-17-021', 28, 'Secret handling and client boundary'],
  ['02', 'TEST-RUN-2026-05-17-028', 26, 'API privacy boundary'],
  ['03', 'TEST-RUN-2026-05-18-019', 26, 'Identity and access control'],
  ['04', 'TEST-RUN-2026-05-18-024', 13, 'Browser security baseline'],
  ['05', 'TEST-RUN-2026-05-18-027', 26, 'Web attack surface baseline'],
  ['06', 'TEST-RUN-2026-05-20-012', 57, 'AI safety boundary'],
  ['07', 'TEST-RUN-2026-05-20-018', 26, 'Rate limits, quotas, abuse and cost control'],
  ['08', 'TEST-RUN-2026-05-20-023', 28, 'Observability privacy boundary'],
  ['09', 'TEST-RUN-2026-05-21-003', 10, 'Security Mini-Prep Review'],
];

const TOOLING_EVIDENCE = [
  ['03_tools_skills/07', 'TEST-RUN-2026-05-20-021', 18, 'Tool execution truth'],
  ['03_tools_skills/09', 'TEST-RUN-2026-05-21-002', 22, 'External tool fallback honesty'],
];

const REVIEW_ARTIFACTS = {
  plan: 'documentation/test-runs/TEST-RUN-2026-05-21-004_plan.json',
  assetFlow: 'documentation/test-runs/TEST-RUN-2026-05-21-004_asset_data_flow.md',
  threatModel: 'documentation/test-runs/TEST-RUN-2026-05-21-004_threat_model.md',
  codeConfig: 'documentation/test-runs/TEST-RUN-2026-05-21-004_code_config_review.md',
  redTeam: 'documentation/test-runs/TEST-RUN-2026-05-21-004_red_team_playbook.md',
  riskRegister: 'documentation/test-runs/TEST-RUN-2026-05-21-004_risk_register.md',
  finalAudit: 'documentation/test-runs/TEST-RUN-2026-05-21-004_final_audit.md',
};

const CRITICAL_FILES = [
  'backend/main.py',
  'backend/dependencies.py',
  'backend/logger_config.py',
  'backend/utils/redaction.py',
  'backend/services/security/injection_detector.py',
  'backend/services/orchestrator/execution_dispatcher.py',
  'backend/services/orchestrator/prompt_registry.py',
  'backend/services/tool_executor.py',
  'backend/services/tool_manager.py',
  'playwright.config.js',
  'package.json',
  'documentation/test-runs/TEST-RUN-2026-05-20-023_privacy_scan.md',
];

const results = [];

function rel(filePath) {
  return path.relative(ROOT, filePath).replaceAll(path.sep, '/');
}

function abs(relativePath) {
  return path.join(ROOT, ...relativePath.split('/'));
}

function readText(relativePath) {
  return fs.readFileSync(abs(relativePath), 'utf-8');
}

function readJson(relativePath) {
  return JSON.parse(readText(relativePath));
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function assertPassingResult(runId, expectedTotal) {
  const resultPath = `documentation/test-results/${runId}_results.json`;
  const result = readJson(resultPath);
  expect(result.status, resultPath).toBe('PASS');
  expect(result.summary.total, resultPath).toBe(expectedTotal);
  expect(result.summary.failed, resultPath).toBe(0);
  expect(result.summary.blocked, resultPath).toBe(0);
  expect(result.artifacts.evidenceFiles.length, resultPath).toBe(expectedTotal);
  return {
    resultPath,
    status: result.status,
    total: result.summary.total,
    passed: result.summary.passed,
    failed: result.summary.failed,
    blocked: result.summary.blocked,
  };
}

function assertArtifact(relativePath, requiredTerms = []) {
  expect(fs.existsSync(abs(relativePath)), relativePath).toBeTruthy();
  const text = readText(relativePath);
  expect(text.trim().length, relativePath).toBeGreaterThan(120);
  for (const term of requiredTerms) {
    expect(text, `${relativePath} must contain ${term}`).toContain(term);
  }
  return { path: relativePath, bytes: Buffer.byteLength(text, 'utf-8') };
}

async function runCase(testCaseId, body) {
  const started = Date.now();
  const evidencePath = path.join(RESULT_DIR, `${testCaseId}_evidence.json`);
  try {
    const evidence = await body();
    const payload = {
      testRunId: TEST_RUN_ID,
      testCaseId,
      result: 'PASS',
      classification: evidence.classification || 'SECURITY_REVIEW_ASSERTION_PASS',
      evidence: evidence.evidence || evidence,
      timestamp: new Date().toISOString(),
    };
    fs.writeFileSync(evidencePath, JSON.stringify(payload, null, 2));
    results.push({
      testCaseId,
      result: 'PASS',
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
      classification: 'SECURITY_REVIEW_ASSERTION_FAIL',
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

test.describe.serial(`${TEST_RUN_ID}: ${TITLE}`, () => {
  test.beforeAll(() => {
    ensureDir(RESULT_DIR);
  });

  test.afterAll(() => {
    const summary = {
      total: results.length,
      passed: results.filter((item) => item.result === 'PASS').length,
      failed: results.filter((item) => item.result !== 'PASS').length,
      blocked: 0,
      manualGateRequired: 0,
    };
    const result = {
      schemaVersion: 'janus.test-result.v1',
      testRunId: TEST_RUN_ID,
      title: TITLE,
      status: summary.failed === 0 ? 'PASS' : 'FAIL',
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

  test('RSV-001: asset and data-flow review is documented', async () => {
    await runCase('RSV-001', async () => ({
      classification: 'ASSET_DATA_FLOW_REVIEW_PASS',
      evidence: assertArtifact(REVIEW_ARTIFACTS.assetFlow, ['Protected assets', 'Trust boundaries', 'Data flow']),
    }));
  });

  test('RSV-002: threat model covers Janus-specific attack paths', async () => {
    await runCase('RSV-002', async () => ({
      classification: 'THREAT_MODEL_REVIEW_PASS',
      evidence: assertArtifact(REVIEW_ARTIFACTS.threatModel, ['Prompt injection', 'Cross-user', 'Mitigation']),
    }));
  });

  test('RSV-003: auth and authorization architecture has passing evidence', async () => {
    await runCase('RSV-003', async () => {
      const main = readText('backend/main.py');
      const deps = readText('backend/dependencies.py');
      expect(main).toContain('Depends(api_key_auth)');
      expect(main).toContain('Security(get_current_user');
      expect(deps).toContain('secrets.compare_digest');
      return {
        classification: 'AUTHZ_REVIEW_PASS',
        evidence: {
          security02: assertPassingResult('TEST-RUN-2026-05-17-028', 26),
          security03: assertPassingResult('TEST-RUN-2026-05-18-019', 26),
          codeReferences: ['backend/main.py', 'backend/dependencies.py'],
        },
      };
    });
  });

  test('RSV-004: secret management and redaction boundaries are validated', async () => {
    await runCase('RSV-004', async () => {
      const redaction = readText('backend/utils/redaction.py');
      const loggerConfig = readText('backend/logger_config.py');
      expect(redaction).toContain('redact_sensitive_text');
      expect(redaction).toContain('Authorization|Cookie|Set-Cookie');
      expect(loggerConfig).toContain('SensitiveRedactionFilter');
      return {
        classification: 'SECRET_REVIEW_PASS',
        evidence: {
          security01: assertPassingResult('TEST-RUN-2026-05-17-021', 28),
          security08: assertPassingResult('TEST-RUN-2026-05-20-023', 28),
          redactionFiles: ['backend/utils/redaction.py', 'backend/logger_config.py'],
        },
      };
    });
  });

  test('RSV-005: API privacy boundary and error shaping are covered', async () => {
    await runCase('RSV-005', async () => ({
      classification: 'API_PRIVACY_REVIEW_PASS',
      evidence: {
        security02: assertPassingResult('TEST-RUN-2026-05-17-028', 26),
        security03: assertPassingResult('TEST-RUN-2026-05-18-019', 26),
        security08: assertPassingResult('TEST-RUN-2026-05-20-023', 28),
        directReviewArtifact: assertArtifact(REVIEW_ARTIFACTS.codeConfig, ['API privacy boundary']),
      },
    }));
  });

  test('RSV-006: AI tooling and prompt-injection controls are covered', async () => {
    await runCase('RSV-006', async () => {
      const dispatcher = readText('backend/services/orchestrator/execution_dispatcher.py');
      const injectionDetector = readText('backend/services/security/injection_detector.py');
      expect(dispatcher).toMatch(/destructive|path|sandbox|injection/i);
      expect(injectionDetector).toMatch(/injection|prompt/i);
      return {
        classification: 'AI_TOOLING_REVIEW_PASS',
        evidence: {
          security05: assertPassingResult('TEST-RUN-2026-05-18-027', 26),
          security06: assertPassingResult('TEST-RUN-2026-05-20-012', 57),
          security07: assertPassingResult('TEST-RUN-2026-05-20-018', 26),
          toolTruth: assertPassingResult('TEST-RUN-2026-05-20-021', 18),
          fallbackHonesty: assertPassingResult('TEST-RUN-2026-05-21-002', 22),
        },
      };
    });
  });

  test('RSV-007: OWASP and browser surface evidence is green', async () => {
    await runCase('RSV-007', async () => {
      const main = readText('backend/main.py');
      expect(main).toContain('Content-Security-Policy');
      expect(main).toContain('X-Content-Type-Options');
      expect(main).toContain('CORSMiddleware');
      return {
        classification: 'OWASP_BROWSER_REVIEW_PASS',
        evidence: {
          security04: assertPassingResult('TEST-RUN-2026-05-18-024', 13),
          security05: assertPassingResult('TEST-RUN-2026-05-18-027', 26),
          headersConfigured: true,
        },
      };
    });
  });

  test('RSV-008: logging, telemetry and audit privacy are reviewed', async () => {
    await runCase('RSV-008', async () => {
      const main = readText('backend/main.py');
      expect(main).toContain('send_default_pii=False');
      expect(main).not.toContain('send_default_pii=True');
      return {
        classification: 'LOGGING_TELEMETRY_REVIEW_PASS',
        evidence: {
          security08: assertPassingResult('TEST-RUN-2026-05-20-023', 28),
          privacyScan: assertArtifact('documentation/test-runs/TEST-RUN-2026-05-20-023_privacy_scan.md', ['Results']),
          sentryPiiDisabled: true,
        },
      };
    });
  });

  test('RSV-009: rate-limit and cost-abuse controls are green', async () => {
    await runCase('RSV-009', async () => ({
      classification: 'RATE_COST_REVIEW_PASS',
      evidence: {
        security07: assertPassingResult('TEST-RUN-2026-05-20-018', 26),
        miniPrepCostMode: assertPassingResult('TEST-RUN-2026-05-21-003', 10),
      },
    }));
  });

  test('RSV-010: deployment configuration is reviewed with explicit watchpoints', async () => {
    await runCase('RSV-010', async () => {
      const packageJson = readJson('package.json');
      const playwrightConfig = readText('playwright.config.js');
      expect(packageJson.scripts['start-backend-only-without-reload']).toContain('uvicorn backend.main:app');
      expect(playwrightConfig).toContain('JANUS_E2E_FAST_MODE');
      return {
        classification: 'DEPLOYMENT_REVIEW_PASS_WITH_WATCHPOINTS',
        notes: 'Production/staging HTTPS, HSTS, domain CORS and account fixtures remain environment-specific watchpoints.',
        evidence: assertArtifact(REVIEW_ARTIFACTS.codeConfig, ['Deployment and operations', 'Watchpoints']),
      };
    });
  });

  test('RSV-011: manual red-team playbook maps attacks to evidence', async () => {
    await runCase('RSV-011', async () => ({
      classification: 'RED_TEAM_PLAYBOOK_REVIEW_PASS',
      evidence: {
        playbook: assertArtifact(REVIEW_ARTIFACTS.redTeam, ['RT-001', 'RT-010', 'Evidence']),
        linkedTooling: TOOLING_EVIDENCE.map(([, runId, total]) => assertPassingResult(runId, total)),
      },
    }));
  });

  test('RSV-012: launch gate decision and risk register are complete', async () => {
    await runCase('RSV-012', async () => {
      const baselines = SECURITY_BASELINE.map(([, runId, total]) => assertPassingResult(runId, total));
      for (const file of CRITICAL_FILES) {
        expect(fs.existsSync(abs(file)), file).toBeTruthy();
      }
      const riskRegister = assertArtifact(REVIEW_ARTIFACTS.riskRegister, [
        'No open Critical',
        'No open High',
        'PASS WITH WATCHPOINTS',
      ]);
      const finalAudit = assertArtifact(REVIEW_ARTIFACTS.finalAudit, ['PASS WITH WATCHPOINTS', TEST_RUN_ID]);
      expect(fs.existsSync(SPEC_PATH)).toBeTruthy();
      return {
        classification: 'LAUNCH_GATE_REVIEW_PASS_WITH_WATCHPOINTS',
        notes: 'No open Critical/High findings remain for the reviewed local scope.',
        evidence: {
          reviewSpec: rel(SPEC_PATH),
          baselineRuns: baselines,
          riskRegister,
          finalAudit,
          criticalFilesReviewed: CRITICAL_FILES,
          decision: 'PASS WITH WATCHPOINTS',
        },
      };
    });
  });
});
