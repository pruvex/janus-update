#!/usr/bin/env node
/**
 * Deterministic TEST SKILL 2 -> TEST SKILL 3 handover generator.
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
    if (key === '--capability') args.capability = value;
  }
  return args;
}

function fail(message) {
  console.error(`HANDOVER INVALID: ${message}`);
  process.exit(1);
}

const args = parseArgs(process.argv);
if (!/^documentation\/TEST_SPEC\/(?:[^\\/]+\/)*[^\\/]+\.md$/.test(args.spec || '')) fail(`Invalid TestSpec: ${args.spec || ''}`);
if (!/^documentation\/test-runs\/TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}_plan\.json$/.test(args.plan || '')) fail(`Invalid TestPlan: ${args.plan || ''}`);
if (!/^TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}$/.test(args.run || '')) fail(`Invalid TargetTestRun: ${args.run || ''}`);
if (!fs.existsSync(args.spec)) fail(`TestSpec not found: ${args.spec}`);
if (!fs.existsSync(args.plan)) fail(`TestPlan not found: ${args.plan}`);

const plan = JSON.parse(fs.readFileSync(args.plan, 'utf8'));
if (plan.testRunId !== args.run) fail(`Plan testRunId mismatch: ${plan.testRunId}`);
if (!Array.isArray(plan.tests)) fail('Plan tests[] missing');

const capability = String(args.capability || plan.title || 'N_A')
  .replace(/[;\r\n]+/g, ' ')
  .replace(/\s+/g, ' ')
  .trim();

process.stdout.write(
  `@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION] Mode=LIVE_VISUAL; ExecutionModel=SWE_1_6; TestSpec=${args.spec}; TestPlan=${args.plan}; TargetTestRun=${args.run}; Capability=${capability}; PrecheckResult=READY_FOR_LIVE_TEST; StrictValidator=TESTPLAN_VALID; GeneratorPlanTests=${plan.tests.length}; ConnectivityMode=PLAYWRIGHT_WEBSERVER_AUTOSTART; ManualJanusStartRequired=NO; Rules=USE_ARTIFACTS_ONLY_EXECUTE_LIVE_TESTS_COLLECT_EVIDENCE_NO_IMPLEMENTATION; ExpectedOutput=TEST_RESULT_PLUS_SINGLE_LINE_HANDOFF_TO_TEST_SKILL_4_WITH_METRICS\n`,
);
