#!/usr/bin/env node
/**
 * Deterministic TEST SKILL 4 -> SKILL 7 handover generator for terminal PASS runs.
 */

import fs from 'node:fs';
import { spawnSync } from 'node:child_process';

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
    if (key === '--backlog-item') args.backlogItem = value;
    if (key === '--task') args.task = value;
    if (key === '--completion-action') args.completionAction = value;
  }
  return args;
}

function fail(message) {
  console.error(`SKILL7 HANDOVER INVALID: ${message}`);
  process.exit(1);
}

function pct(numerator, denominator) {
  if (!denominator) return '0.00';
  return ((numerator / denominator) * 100).toFixed(2);
}

function cleanToken(value, fallback) {
  return String(value || fallback).replace(/[;\r\n]+/g, '_').trim() || fallback;
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

if (!fs.existsSync(args.result)) {
  const created = spawnSync(process.execPath, [
    'tests/e2e/generator/create-test-result-md.mjs',
    '--result-json',
    args.resultJson,
    '--out',
    args.result,
  ], { encoding: 'utf8' });
  if (created.status !== 0) fail(`TestResult not found and could not create md: ${created.stderr || created.stdout}`);
}

const plan = JSON.parse(fs.readFileSync(args.plan, 'utf8'));
const result = JSON.parse(fs.readFileSync(args.resultJson, 'utf8'));
if (plan.testRunId !== args.run) fail(`Plan testRunId mismatch: ${plan.testRunId}`);
if (result.testRunId !== args.run) fail(`Result testRunId mismatch: ${result.testRunId}`);
if (!Array.isArray(plan.tests)) fail('Plan tests[] missing');
if (!Array.isArray(result.results)) fail('Result results[] missing');

const summary = result.summary || {};
const total = Number(summary.total || result.results.length || 0);
const passed = Number(summary.passed || result.results.filter((entry) => entry.result === 'PASS').length);
const failed = Number(summary.failed || result.results.filter((entry) => entry.result === 'FAIL').length);
const blocked = Number(summary.blocked || result.results.filter((entry) => entry.result === 'BLOCKED').length);
const manualGate = Number(summary.manualGateRequired || result.results.filter((entry) => entry.result === 'MANUAL_GATE').length);

if (result.status !== 'PASS') fail(`Terminal PASS required, got ${result.status || 'UNKNOWN'}`);
if (total <= 0 || passed !== total || failed !== 0 || blocked !== 0 || manualGate !== 0) {
  fail(`Terminal PASS summary required, got total=${total} passed=${passed} failed=${failed} blocked=${blocked} manualGate=${manualGate}`);
}

const testById = new Map(plan.tests.map((test) => [test.id, test]));
const providerPassRates = groupPassRates(result.results, testById, (_entry, test) => test?.provider) || 'N_A';
const typePassRates = groupPassRates(result.results, testById, (_entry, test) => test?.type) || 'N_A';
const backlogItem = /^BACKLOG-\d{3}$/.test(args.backlogItem || '') ? args.backlogItem : 'N_A';
const task = cleanToken(args.task, 'N_A');
const completionAction = cleanToken(
  args.completionAction,
  backlogItem === 'N_A' ? 'RECORD_TEST_PIPELINE_PASS_AND_SYNC_DOCUMENTATION' : 'MARK_BACKLOG_DONE_AND_SYNC_DASHBOARD',
);

process.stdout.write(
  `@[/SKILL 7 - DOKUMENTATIONSUPDATE] Mode=COMPLETE_TASK; ExecutionModel=SWE_1_6; BacklogItem=${backlogItem}; Task=${task}; TestSpec=${args.spec}; TestPlan=${args.plan}; TestResult=${args.result}; TestResultJson=${args.resultJson}; TargetTestRun=${args.run}; ResultStatus=PASS; TotalTests=${total}; Passed=${passed}; Failed=0; Blocked=0; ManualGate=0; PassRatePct=${pct(passed, total)}; ProviderPassRatePct=${providerPassRates}; TypePassRatePct=${typePassRates}; Findings=NONE; CompletionAction=${completionAction}; Rules=USE_ARTIFACTS_ONLY_RECORD_COMPLETED_ONLY_NO_PENDING_RECORD; ExpectedOutput=TASK_COMPLETED_DASHBOARD_SYNCED\n`,
);
