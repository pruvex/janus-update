#!/usr/bin/env node
/**
 * Deterministic TEST SKILL 3 -> TEST SKILL 4 handover generator.
 */

import fs from 'node:fs';

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (key === '--spec') args.spec = value;
    if (key === '--plan') args.plan = value;
    if (key === '--run') args.run = value;
    if (key === '--result') args.result = value;
    if (key === '--result-json') args.resultJson = value;
    if (key === '--failure-code') args.failureCode = value;
  }
  return args;
}

function fail(message) {
  console.error(`HANDOVER INVALID: ${message}`);
  process.exit(1);
}

function pct(numerator, denominator) {
  if (!denominator) return '0.00';
  return ((numerator / denominator) * 100).toFixed(2);
}

function groupPassRates(results, testById, keyFn) {
  const groups = new Map();
  for (const entry of results) {
    const test = testById.get(entry.testCaseId);
    const key = keyFn(entry, test);
    if (!key) continue;
    const current = groups.get(key) || { total: 0, passed: 0 };
    current.total += 1;
    if (entry.result === 'PASS') current.passed += 1;
    groups.set(key, current);
  }
  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}:${pct(value.passed, value.total)}`)
    .join(',');
}

const args = parseArgs(process.argv);
if (!/^documentation\/TEST_SPEC\/(?:[^\\/]+\/)*[^\\/]+\.md$/.test(args.spec || '')) fail(`Invalid TestSpec: ${args.spec || ''}`);
if (!/^documentation\/test-runs\/TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}_plan\.json$/.test(args.plan || '')) fail(`Invalid TestPlan: ${args.plan || ''}`);
if (!/^TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}$/.test(args.run || '')) fail(`Invalid TargetTestRun: ${args.run || ''}`);
if (!/^documentation\/test-results\/TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}_results\.md$/.test(args.result || '')) fail(`Invalid TestResult: ${args.result || ''}`);
if (!/^documentation\/test-results\/TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}_results\.json$/.test(args.resultJson || '')) fail(`Invalid TestResultJson: ${args.resultJson || ''}`);
if (!fs.existsSync(args.plan)) fail(`TestPlan not found: ${args.plan}`);
if (!fs.existsSync(args.resultJson)) fail(`TestResultJson not found: ${args.resultJson}`);

const plan = JSON.parse(fs.readFileSync(args.plan, 'utf8'));
const result = JSON.parse(fs.readFileSync(args.resultJson, 'utf8'));
if (plan.testRunId !== args.run) fail(`Plan testRunId mismatch: ${plan.testRunId}`);
if (result.testRunId !== args.run) fail(`Result testRunId mismatch: ${result.testRunId}`);
if (!Array.isArray(plan.tests)) fail('Plan tests[] missing');
if (!Array.isArray(result.results)) fail('Result results[] missing');
if (!fs.existsSync(args.result)) {
  const { spawnSync } = await import('node:child_process');
  const created = spawnSync(process.execPath, [
    'tests/e2e/generator/create-test-result-md.mjs',
    '--result-json',
    args.resultJson,
    '--out',
    args.result,
  ], { encoding: 'utf8' });
  if (created.status !== 0) fail(`TestResult not found and could not create md: ${created.stderr || created.stdout}`);
}

const testById = new Map(plan.tests.map((test) => [test.id, test]));
const summary = result.summary || {};
const total = Number(summary.total || result.results.length || 0);
const passed = Number(summary.passed || result.results.filter((entry) => entry.result === 'PASS').length);
const failed = Number(summary.failed || result.results.filter((entry) => entry.result === 'FAIL').length);
const blocked = Number(summary.blocked || result.results.filter((entry) => entry.result === 'BLOCKED').length);
const manualGate = Number(summary.manualGateRequired || result.results.filter((entry) => entry.result === 'MANUAL_GATE').length);
const normalizedInputFailureCode = (args.failureCode || '').replace(/[;\r\n]+/g, '_').trim();
const failureCode = result.status === 'PASS' && failed === 0 && blocked === 0 && manualGate === 0
  ? 'NONE'
  : (normalizedInputFailureCode && !/^N\/?A$/i.test(normalizedInputFailureCode) ? normalizedInputFailureCode : 'N_A');
const blockerCodes = new Set([
  'INFRASTRUCTURE_OFFLINE',
  'BACKEND_HEALTH_FAIL',
  'FRONTEND_NOT_READY',
  'E2E_AUTH_TOKEN_MISSING',
  'JANUS_CONFIG_OR_AUTH_MISSING',
]);
if (blockerCodes.has(failureCode)) {
  fail(`${failureCode} is infrastructure/auth/runner setup, not finding triage. Route to SKILL 5 FEATURE DEBUG with TestResult=N/A.`);
}
if (total > 0 && blocked === total && failed === total) {
  fail('All tests are blocked/failed by setup; do not create TEST SKILL 4 handover. Route to SKILL 5 FEATURE DEBUG.');
}
const providerPassRates = groupPassRates(result.results, testById, (_entry, test) => test?.provider);
const typePassRates = groupPassRates(result.results, testById, (_entry, test) => test?.type);

process.stdout.write(
  `@[/TEST SKILL 4 – FINDING TRIAGE AND ROUTING] Mode=FINDING_TRIAGE; ExecutionModel=SWE_1_6; TestSpec=${args.spec}; TestPlan=${args.plan}; TestResult=${args.result}; TestResultJson=${args.resultJson}; TargetTestRun=${args.run}; ResultStatus=${result.status || 'UNKNOWN'}; TotalTests=${total}; Passed=${passed}; Failed=${failed}; Blocked=${blocked}; ManualGate=${manualGate}; PassRatePct=${pct(passed, total)}; FailRatePct=${pct(failed, total)}; BlockedRatePct=${pct(blocked, total)}; ProviderPassRatePct=${providerPassRates || 'N_A'}; TypePassRatePct=${typePassRates || 'N_A'}; FailureCode=${failureCode}; ChangedFiles=NONE; Rules=USE_RESULT_ARTIFACTS_ONLY_PRESERVE_FAILURE_CODES_NO_IMPLEMENTATION; ExpectedOutput=FINDINGS_TRIAGED_OR_NO_FINDINGS\n`,
);
