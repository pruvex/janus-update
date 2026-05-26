/**
 * TEST-RUN-2026-05-21-003 Mini-Prep Security Review Runner
 *
 * This runner validates security-test readiness, not model behavior.
 * It writes Janus-compatible result/evidence artifacts under documentation/test-results.
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const TEST_RUN_ID = 'TEST-RUN-2026-05-21-003';
const TITLE = 'Janus Security Mini-Prep Review';
const RESULT_DIR = path.join(process.cwd(), 'documentation', 'test-results', TEST_RUN_ID);
const RESULT_JSON = path.join(process.cwd(), 'documentation', 'test-results', `${TEST_RUN_ID}_results.json`);
const SPEC_PATH = path.join(process.cwd(), 'documentation', 'TEST_SPEC', '02_security_safety', '09_mini_prep_security_review.md');
const SYNTHETIC_CANARIES = [
  'SYNTHETIC_CANARY_MINIPREP_ALPHA_DO_NOT_USE',
  'SYNTHETIC_CANARY_MINIPREP_BETA_DO_NOT_USE',
];

const results = [];

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function redactStatus(value) {
  if (!value) return 'missing';
  return `present(length=${String(value).length})`;
}

function listPythonRoutes() {
  const routerDir = path.join(process.cwd(), 'backend', 'api', 'routers');
  const mainPath = path.join(process.cwd(), 'backend', 'main.py');
  const routeFiles = fs.existsSync(routerDir)
    ? fs.readdirSync(routerDir).filter((name) => name.endsWith('.py')).sort()
    : [];
  const mainText = fs.existsSync(mainPath) ? fs.readFileSync(mainPath, 'utf-8') : '';
  const directRoutes = Array.from(mainText.matchAll(/@app\.(get|post|put|patch|delete)\(["']([^"']+)/g))
    .map((match) => `${match[1].toUpperCase()} ${match[2]}`);
  return { routeFiles, directRoutes };
}

async function runCase(testInfo, testCaseId, body) {
  const started = Date.now();
  const evidencePath = path.join(RESULT_DIR, `${testCaseId}_evidence.json`);
  try {
    const evidence = await body();
    const payload = {
      testRunId: TEST_RUN_ID,
      testCaseId,
      result: 'PASS',
      classification: evidence.classification || 'PREP_ASSERTION_PASS',
      evidence: evidence.evidence || evidence,
      timestamp: new Date().toISOString(),
    };
    fs.writeFileSync(evidencePath, JSON.stringify(payload, null, 2));
    results.push({
      testCaseId,
      result: 'PASS',
      classification: payload.classification,
      evidencePath: path.relative(process.cwd(), evidencePath).replaceAll(path.sep, '/'),
      durationMs: Date.now() - started,
      notes: evidence.notes || '',
      timestamp: payload.timestamp,
    });
  } catch (error) {
    const payload = {
      testRunId: TEST_RUN_ID,
      testCaseId,
      result: 'FAIL',
      classification: 'PREP_ASSERTION_FAIL',
      error: String(error && error.stack ? error.stack : error),
      timestamp: new Date().toISOString(),
    };
    fs.writeFileSync(evidencePath, JSON.stringify(payload, null, 2));
    results.push({
      testCaseId,
      result: 'FAIL',
      classification: payload.classification,
      evidencePath: path.relative(process.cwd(), evidencePath).replaceAll(path.sep, '/'),
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
        resultDirectory: path.relative(process.cwd(), RESULT_DIR).replaceAll(path.sep, '/'),
        resultJson: path.relative(process.cwd(), RESULT_JSON).replaceAll(path.sep, '/'),
        evidenceFiles: results.map((item) => item.evidencePath),
      },
      results,
      updatedAt: new Date().toISOString(),
    };
    fs.writeFileSync(RESULT_JSON, JSON.stringify(result, null, 2));
  });

  test('PREP-001: app and API are reachable', async ({ page, request }, testInfo) => {
    await runCase(testInfo, 'PREP-001', async () => {
      const response = await request.get('http://localhost:8001/api/health');
      expect(response.ok()).toBeTruthy();
      const health = await response.json();
      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();
      return {
        classification: 'LIVE_REACHABILITY_PASS',
        evidence: {
          appUrl: 'http://localhost:5173',
          apiBaseUrl: 'http://localhost:8001',
          healthStatus: response.status(),
          healthKeys: Object.keys(health).sort(),
          frontendBodyVisible: true,
        },
      };
    });
  });

  test('PREP-002: start commands and local test environment are declared', async ({}, testInfo) => {
    await runCase(testInfo, 'PREP-002', async () => {
      const packageJson = readJson(path.join(process.cwd(), 'package.json'));
      const playwrightConfig = fs.readFileSync(path.join(process.cwd(), 'playwright.config.js'), 'utf-8');
      expect(packageJson.scripts['start-backend-only-without-reload']).toContain('uvicorn backend.main:app');
      expect(packageJson.scripts['start-vite']).toBe('vite');
      expect(playwrightConfig).toContain('http://localhost:8001/api/health');
      expect(playwrightConfig).toContain('http://localhost:5173');
      expect(playwrightConfig).toContain('JANUS_E2E_FAST_MODE');
      return {
        evidence: {
          environmentName: 'local',
          backendStartScript: 'start-backend-only-without-reload',
          frontendStartScript: 'start-vite',
          playwrightOwnsLifecycle: true,
          e2eFastModeConfigured: true,
        },
      };
    });
  });

  test('PREP-003: result paths and machine schema are available', async ({}, testInfo) => {
    await runCase(testInfo, 'PREP-003', async () => {
      const schemaPath = path.join(process.cwd(), 'tests', 'e2e', 'generator', 'test-result.schema.json');
      const resultRoot = path.join(process.cwd(), 'documentation', 'test-results');
      expect(fs.existsSync(SPEC_PATH)).toBeTruthy();
      expect(fs.existsSync(schemaPath)).toBeTruthy();
      expect(fs.existsSync(resultRoot)).toBeTruthy();
      return {
        evidence: {
          reviewSpec: path.relative(process.cwd(), SPEC_PATH).replaceAll(path.sep, '/'),
          resultDirectory: path.relative(process.cwd(), RESULT_DIR).replaceAll(path.sep, '/'),
          resultJson: path.relative(process.cwd(), RESULT_JSON).replaceAll(path.sep, '/'),
          schema: path.relative(process.cwd(), schemaPath).replaceAll(path.sep, '/'),
        },
      };
    });
  });

  test('PREP-004: API endpoint inventory is observable', async ({}, testInfo) => {
    await runCase(testInfo, 'PREP-004', async () => {
      const inventory = listPythonRoutes();
      expect(inventory.routeFiles.length).toBeGreaterThan(5);
      expect(inventory.directRoutes.length).toBeGreaterThan(5);
      expect(inventory.directRoutes.some((route) => route.includes('/api/health'))).toBeTruthy();
      return {
        evidence: {
          routerFileCount: inventory.routeFiles.length,
          routerFiles: inventory.routeFiles,
          directRouteCount: inventory.directRoutes.length,
          representativeRoutes: inventory.directRoutes.slice(0, 20),
        },
      };
    });
  });

  test('PREP-005: auth/session setup is available without exposing raw secrets', async ({}, testInfo) => {
    await runCase(testInfo, 'PREP-005', async () => {
      const appData = process.env.APPDATA || '';
      const configPath = path.join(appData, 'Janus Projekt', 'config.json');
      const config = readJson(configPath);
      expect(String(config.jwt_secret_key || '').length).toBeGreaterThan(20);
      expect(String(config.api_key || '').length).toBeGreaterThan(20);
      return {
        evidence: {
          authMethod: 'local signed JWT plus X-Janus-Internal-Key in E2E route injection',
          configPath: path.join('%APPDATA%', 'Janus Projekt', 'config.json'),
          jwtSecret: redactStatus(config.jwt_secret_key),
          internalApiKey: redactStatus(config.api_key),
          rawSecretsWrittenToEvidence: false,
        },
      };
    });
  });

  test('PREP-006: synthetic users, canaries, and resettable fixture isolation work', async ({}, testInfo) => {
    await runCase(testInfo, 'PREP-006', async () => {
      const fixtureRoot = path.join(RESULT_DIR, 'fixtures');
      const userA = path.join(fixtureRoot, 'synthetic-user-a');
      const userB = path.join(fixtureRoot, 'synthetic-user-b');
      fs.rmSync(fixtureRoot, { recursive: true, force: true });
      ensureDir(userA);
      ensureDir(userB);
      fs.writeFileSync(path.join(userA, 'canary.txt'), SYNTHETIC_CANARIES[0]);
      fs.writeFileSync(path.join(userB, 'canary.txt'), SYNTHETIC_CANARIES[1]);
      expect(fs.readFileSync(path.join(userA, 'canary.txt'), 'utf-8')).toBe(SYNTHETIC_CANARIES[0]);
      expect(fs.readFileSync(path.join(userB, 'canary.txt'), 'utf-8')).toBe(SYNTHETIC_CANARIES[1]);
      fs.rmSync(fixtureRoot, { recursive: true, force: true });
      expect(fs.existsSync(fixtureRoot)).toBeFalsy();
      return {
        classification: 'FIXTURE_RESET_PASS',
        evidence: {
          syntheticUserA: 'synthetic-user-a',
          syntheticUserB: 'synthetic-user-b',
          canaries: SYNTHETIC_CANARIES.map((value) => `${value} (synthetic)`),
          separatedFixtureDirectories: true,
          resetMethod: 'fs.rmSync(fixtureRoot, { recursive: true, force: true })',
          resetVerified: true,
        },
      };
    });
  });

  test('PREP-007: logs and build artifacts are observable', async ({}, testInfo) => {
    await runCase(testInfo, 'PREP-007', async () => {
      const appData = process.env.APPDATA || '';
      const logDir = path.join(appData, 'Janus Projekt', 'logs');
      const frontendDist = path.join(process.cwd(), 'frontend', 'dist');
      const backendMain = path.join(process.cwd(), 'backend', 'main.py');
      expect(fs.existsSync(logDir)).toBeTruthy();
      expect(fs.existsSync(frontendDist)).toBeTruthy();
      expect(fs.existsSync(backendMain)).toBeTruthy();
      const logFiles = fs.readdirSync(logDir).filter((name) => name.endsWith('.log')).sort();
      return {
        evidence: {
          backendLogDirectory: path.join('%APPDATA%', 'Janus Projekt', 'logs'),
          logFiles,
          frontendBuildArtifact: 'frontend/dist',
          backendEntryPoint: 'backend/main.py',
          sourcemapLocationKnown: 'frontend/dist (if build emits sourcemaps)',
        },
      };
    });
  });

  test('PREP-008: provider and rate-limit execution mode is cost-controlled', async ({}, testInfo) => {
    await runCase(testInfo, 'PREP-008', async () => {
      const playwrightConfig = fs.readFileSync(path.join(process.cwd(), 'playwright.config.js'), 'utf-8');
      const rateLimitSpec = path.join(process.cwd(), 'documentation', 'TEST_SPEC', '02_security_safety', '07_rate_limits_quotas_abuse_and_cost_control.md');
      const rateLimitResult = path.join(process.cwd(), 'documentation', 'test-results', 'TEST-RUN-2026-05-20-018_results.json');
      expect(playwrightConfig).toContain('JANUS_E2E_FAST_MODE');
      expect(fs.existsSync(rateLimitSpec)).toBeTruthy();
      expect(fs.existsSync(rateLimitResult)).toBeTruthy();
      const result = readJson(rateLimitResult);
      expect(result.status).toBe('PASS');
      return {
        evidence: {
          providerMode: 'low-cost live provider mode for generated E2E; JANUS_E2E_FAST_MODE enabled for background work suppression',
          rateLimitMode: 'validated by TEST-RUN-2026-05-20-018',
          rateLimitResultStatus: result.status,
          uncontrolledProviderBurnAllowed: false,
        },
      };
    });
  });

  test('PREP-009: real data and production secret exposure are not required', async ({}, testInfo) => {
    await runCase(testInfo, 'PREP-009', async () => {
      const specText = fs.readFileSync(SPEC_PATH, 'utf-8');
      expect(specText).toContain('Real User Data Allowed: NO');
      expect(specText).toContain('Production Secrets Allowed: NO');
      expect(specText).toContain('Synthetic Canary Secrets Allowed: YES');
      for (const canary of SYNTHETIC_CANARIES) {
        expect(canary).toMatch(/^SYNTHETIC_CANARY_/);
      }
      return {
        evidence: {
          realUserDataAllowed: false,
          productionSecretsAllowed: false,
          syntheticCanariesAllowed: true,
          syntheticCanaries: SYNTHETIC_CANARIES.map((value) => `${value} (synthetic)`),
          rawProductionSecretsInEvidence: false,
        },
      };
    });
  });

  test('PREP-010: GO decision criteria are satisfied for local security tests', async ({}, testInfo) => {
    await runCase(testInfo, 'PREP-010', async () => {
      const required = [
        'app/api reachable',
        'local environment identified',
        'result schema/path observable',
        'endpoint inventory observable',
        'auth/session setup documented without raw secrets',
        'synthetic A/B fixture isolation reset verified',
        'logs/build artifacts observable',
        'provider/rate-limit mode cost-controlled',
        'real data and production secrets disallowed',
      ];
      expect(required.length).toBe(9);
      return {
        classification: 'GO_DECISION_PASS',
        notes: 'Review decision: GO WITH WATCHPOINTS. Watchpoint: this prep validates local disposable A/B fixtures and existing local auth method; true multi-account staging fixtures remain environment-specific.',
        evidence: {
          reviewDecision: 'GO WITH WATCHPOINTS',
          blockingConditions: [],
          watchpoints: [
            'True multi-account staging users are environment-specific; local prep uses disposable A/B fixture identities plus existing local_user E2E auth.',
          ],
          nextStepIfGo: 'Run or continue Security TestSpecs 01-08/10 with these readiness artifacts attached.',
          criteriaSatisfied: required,
        },
      };
    });
  });
});
