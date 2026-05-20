#!/usr/bin/env node
/**
 * Create a deterministic Markdown summary from janus.test-result.v1 JSON.
 */

import fs from 'node:fs';

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (key === '--result-json') args.resultJson = value;
    if (key === '--out') args.out = value;
  }
  return args;
}

function fail(message) {
  console.error(`RESULT MD INVALID: ${message}`);
  process.exit(1);
}

function pct(numerator, denominator) {
  if (!denominator) return '0.00';
  return ((numerator / denominator) * 100).toFixed(2);
}

const args = parseArgs(process.argv);
if (!/^documentation\/test-results\/TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}_results\.json$/.test(args.resultJson || '')) {
  fail(`Invalid result json path: ${args.resultJson || ''}`);
}
if (!/^documentation\/test-results\/TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}_results\.md$/.test(args.out || '')) {
  fail(`Invalid output path: ${args.out || ''}`);
}
if (!fs.existsSync(args.resultJson)) fail(`Result json not found: ${args.resultJson}`);

const result = JSON.parse(fs.readFileSync(args.resultJson, 'utf8'));
if (result.schemaVersion !== 'janus.test-result.v1') fail(`Unsupported schemaVersion: ${result.schemaVersion || ''}`);
if (!Array.isArray(result.results)) fail('results[] missing');

const summary = result.summary || {};
const total = Number(summary.total || result.results.length || 0);
const passed = Number(summary.passed || result.results.filter((entry) => entry.result === 'PASS').length);
const failed = Number(summary.failed || result.results.filter((entry) => entry.result === 'FAIL').length);
const blocked = Number(summary.blocked || result.results.filter((entry) => entry.result === 'BLOCKED').length);
const manualGate = Number(summary.manualGateRequired || result.results.filter((entry) => entry.result === 'MANUAL_GATE_REQUIRED').length);
const failedRows = result.results
  .filter((entry) => entry.result !== 'PASS')
  .map((entry) => `| ${entry.testCaseId} | ${entry.result} | ${entry.classification} | ${entry.evidencePath} | ${entry.notes || ''} |`)
  .join('\n') || '| none | PASS | N/A | N/A | N/A |';
const allRows = result.results
  .map((entry) => `| ${entry.testCaseId} | ${entry.result} | ${entry.classification} | ${entry.evidencePath} |`)
  .join('\n');

const markdown = `# TEST RUN RESULT - ${result.testRunId}

## Metadata

- **TestRun ID:** ${result.testRunId}
- **Title:** ${result.title || 'N/A'}
- **Status:** ${result.status || 'UNKNOWN'}
- **Result JSON:** ${args.resultJson}
- **Result Directory:** ${result.artifacts?.resultDirectory || 'N/A'}
- **Updated At:** ${result.updatedAt || 'N/A'}

## Summary

- **Total Tests:** ${total}
- **Passed:** ${passed}
- **Failed:** ${failed}
- **Blocked:** ${blocked}
- **Manual Gate Required:** ${manualGate}
- **PassRatePct:** ${pct(passed, total)}
- **FailRatePct:** ${pct(failed, total)}
- **BlockedRatePct:** ${pct(blocked, total)}

## Failed Or Non-Pass Tests

| TestCase | Result | Classification | Evidence | Notes |
|---|---|---|---|---|
${failedRows}

## All Tests

| TestCase | Result | Classification | Evidence |
|---|---|---|---|
${allRows}
`;

fs.writeFileSync(args.out, markdown, 'utf8');
process.stdout.write(`${args.out}\n`);
