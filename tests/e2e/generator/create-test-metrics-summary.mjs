#!/usr/bin/env node
/**
 * Deterministic human-readable metrics summary for TEST SKILL 3 outputs.
 */

import fs from 'node:fs';

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (key === '--plan') args.plan = value;
    if (key === '--result-json') args.resultJson = value;
  }
  return args;
}

function fail(message) {
  console.error(`METRICS SUMMARY INVALID: ${message}`);
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
    .map(([key, value]) => `${key} ${pct(value.passed, value.total)}%`)
    .join(', ');
}

const args = parseArgs(process.argv);
if (!args.plan || !fs.existsSync(args.plan)) fail(`Plan not found: ${args.plan || ''}`);
if (!args.resultJson || !fs.existsSync(args.resultJson)) fail(`ResultJson not found: ${args.resultJson || ''}`);

const plan = JSON.parse(fs.readFileSync(args.plan, 'utf8'));
const result = JSON.parse(fs.readFileSync(args.resultJson, 'utf8'));
if (plan.testRunId !== result.testRunId) fail(`TestRun mismatch: plan=${plan.testRunId} result=${result.testRunId}`);
if (!Array.isArray(plan.tests)) fail('Plan tests[] missing');
if (!Array.isArray(result.results)) fail('Result results[] missing');

const summary = result.summary || {};
const total = Number(summary.total || result.results.length || 0);
const passed = Number(summary.passed || result.results.filter((entry) => entry.result === 'PASS').length);
const failed = Number(summary.failed || result.results.filter((entry) => entry.result === 'FAIL').length);
const blocked = Number(summary.blocked || result.results.filter((entry) => entry.result === 'BLOCKED').length);
const testById = new Map(plan.tests.map((test) => [test.id, test]));
const provider = groupPassRates(result.results, testById, (_entry, test) => test?.provider) || 'N_A';
const type = groupPassRates(result.results, testById, (_entry, test) => test?.type) || 'N_A';

process.stdout.write(`Metrik-Summary:
- Overall Green: ${pct(passed, total)}%
- Overall Red: ${pct(failed, total)}%
- Blocked: ${pct(blocked, total)}%
- Provider Green: ${provider}
- Type Green: ${type}
`);
