#!/usr/bin/env node
/**
 * Deterministic TEST SKILL 3 preflight.
 *
 * It generates the runner, validates it, checks Playwright webServer ownership,
 * and decides whether Skill 3 should block or ask for OK START LIVE TEST.
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
  }
  return args;
}

function fail(message, detail = '') {
  console.error(`LIVE TEST AUTOMATION BLOCKED\nBlock Reason: ${message}`);
  if (detail) console.error(`\nDetail:\n${detail}`);
  process.exit(1);
}

function runNode(args) {
  const result = spawnSync(process.execPath, args, { encoding: 'utf-8' });
  return {
    ok: result.status === 0,
    output: `${result.stdout || ''}${result.stderr || ''}`.trim(),
  };
}

function webServerOwnsPlanUrls(plan) {
  if (!fs.existsSync('playwright.config.js')) return false;
  const config = fs.readFileSync('playwright.config.js', 'utf-8');
  const frontendUrl = String(plan.baseUrl || '').replace(/\/$/, '');
  const backendUrl = String(plan.backendHealthUrl || '');
  return (
    /webServer\s*:/s.test(config) &&
    frontendUrl &&
    backendUrl &&
    config.includes(frontendUrl) &&
    config.includes(backendUrl)
  );
}

const args = parseArgs(process.argv);
if (!/^documentation\/TEST_SPEC\/(?:[^\\/]+\/)*[^\\/]+\.md$/.test(args.spec || '')) fail(`INVALID_TESTSPEC_PATH: ${args.spec || ''}`);
if (!/^documentation\/test-runs\/TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}_plan\.json$/.test(args.plan || '')) fail(`INVALID_TESTPLAN_PATH: ${args.plan || ''}`);
if (!/^TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}$/.test(args.run || '')) fail(`INVALID_TEST_RUN_ID: ${args.run || ''}`);
if (!fs.existsSync(args.plan)) fail(`TESTPLAN_NOT_FOUND: ${args.plan}`);

const plan = JSON.parse(fs.readFileSync(args.plan, 'utf-8'));
if (plan.testRunId !== args.run) fail(`TEST_RUN_ID_MISMATCH: plan=${plan.testRunId} input=${args.run}`);

const runnerPath = `tests/e2e/generated/${args.run}.live.spec.js`;

const generator = runNode(['tests/e2e/generator/generate-live-runner.mjs', '--plan', args.plan, '--out', runnerPath]);
if (!generator.ok) fail('GENERATOR_NOT_READY', generator.output);

const validator = runNode(['tests/e2e/generator/validate-runner.mjs', '--plan', args.plan, '--runner', runnerPath]);
if (!validator.ok) fail('GENERATOR_VALIDATION_FAILED', validator.output);

const webServerOwned = webServerOwnsPlanUrls(plan);
if (!webServerOwned) {
  const handover = runNode([
    'tests/e2e/generator/create-test-skill3-retest-handover.mjs',
    '--spec',
    args.spec,
    '--plan',
    args.plan,
    '--run',
    args.run,
    '--reason',
    'LIVE_TEST_BLOCKED_INFRASTRUCTURE_OFFLINE',
    '--action',
    'START_JANUS_DEV_SERVER_WITH_NPM_RUN_START_DEV',
  ]);
  console.log('LIVE TEST BLOCKED — INFRASTRUCTURE OFFLINE');
  console.log(`Blocker: Keine passende Playwright webServer-Konfiguration fuer ${plan.baseUrl} und ${plan.backendHealthUrl}.`);
  console.log('Connectivity-Guard: FAIL');
  console.log('');
  if (handover.output) console.log(handover.output);
  process.exit(2);
}

console.log('LIVE JANUS AUTOMATION READY');
console.log(`TestRun: ${args.run}`);
console.log('Generator: SUCCESS');
console.log('Validator: PASSED');
console.log('Connectivity-Guard: PLAYWRIGHT_WEBSERVER_AUTOSTART_READY');
console.log('Server Lifecycle: Playwright webServer starts backend/frontend automatically');
console.log('Manual Janus Start Required: NEIN');
console.log(`Runner: ${runnerPath}`);
console.log(`Tests: ${plan.tests.length}`);
console.log('');
console.log('Alle Tests validiert. Bereit fuer LIVE_VISUAL Dauerlauf.');
console.log('');
console.log('Antworte mit: OK START LIVE TEST');
