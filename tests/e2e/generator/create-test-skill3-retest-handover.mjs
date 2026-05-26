#!/usr/bin/env node
/**
 * Deterministic TEST SKILL 3 retest handover generator.
 */

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (key === '--spec') args.spec = value;
    if (key === '--plan') args.plan = value;
    if (key === '--run') args.run = value;
    if (key === '--reason') args.reason = value;
    if (key === '--action') args.action = value;
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
const reason = (args.reason || 'LIVE_TEST_BLOCKED').replace(/[;\r\n]+/g, '_').trim();
const action = (args.action || 'RETRY_AFTER_FIX').replace(/[;\r\n]+/g, '_').trim();

process.stdout.write(
  `@[/TEST SKILL 3 – LIVE JANUS TEST EXECUTION] Mode=LIVE_RETEST; ExecutionModel=SWE_1_6; TestSpec=${args.spec}; TestPlan=${args.plan}; TestResult=N/A; TargetTestRun=${args.run}; PreviousStatus=${reason}; RequiredAction=${action}; Rules=USE_SAME_ARTIFACTS_VALIDATE_PREFLIGHT_NO_IMPLEMENTATION; ExpectedOutput=OK_START_LIVE_TEST_OR_LIVE_TEST_BLOCKED\n`,
);
