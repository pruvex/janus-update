#!/usr/bin/env node
/**
 * Deterministic TEST SKILL 1 -> TEST SKILL 2 handover generator.
 *
 * Usage:
 *   node tests/e2e/generator/create-test-skill2-handover.mjs \
 *     --plan documentation/test-runs/TEST-RUN-YYYY-MM-DD-NNN_plan.json \
 *     --spec documentation/TEST_SPEC/01_core_system/foo.md
 *
 * The script validates the TestPlan first. If validation fails, it exits non-zero
 * and emits no copy block.
 */

import fs from 'node:fs';
import { spawnSync } from 'node:child_process';

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    if (argv[i] === '--plan') args.plan = argv[i + 1];
    if (argv[i] === '--spec') args.spec = argv[i + 1];
  }
  return args;
}

function fail(message) {
  console.error(`HANDOVER INVALID: ${message}`);
  process.exit(1);
}

function assertRelativeArtifactPath(label, value, pattern) {
  if (!value) fail(`Missing ${label}`);
  if (/^[A-Za-z]:[\\/]/.test(value)) fail(`${label} must not be an absolute Windows path: ${value}`);
  if (!pattern.test(value)) fail(`${label} has invalid artifact path: ${value}`);
}

const args = parseArgs(process.argv);
assertRelativeArtifactPath('TestPlan', args.plan, /^documentation\/test-runs\/TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}_plan\.json$/);
assertRelativeArtifactPath('TestSpec', args.spec, /^documentation\/TEST_SPEC\/(?:[^\\/]+\/)*[^\\/]+\.md$/);

if (!fs.existsSync(args.plan)) fail(`TestPlan not found: ${args.plan}`);
if (!fs.existsSync(args.spec)) fail(`TestSpec not found: ${args.spec}`);

const validator = spawnSync(
  process.execPath,
  ['tests/e2e/generator/validate-test-plan.mjs', '--plan', args.plan],
  { encoding: 'utf-8' },
);

if (validator.status !== 0) {
  const output = `${validator.stdout || ''}${validator.stderr || ''}`.trim();
  fail(`TestPlan validator failed. ${output}`);
}

const plan = JSON.parse(fs.readFileSync(args.plan, 'utf-8'));
if (!plan.testRunId) fail('Validated plan is missing testRunId');
if (!args.plan.includes(`${plan.testRunId}_plan.json`)) {
  fail(`Plan path does not match testRunId ${plan.testRunId}: ${args.plan}`);
}

const capability = (plan.title || 'N/A').replace(/[;\r\n]+/g, ' ').trim();
const parallel = plan.parallelization || {};
const recommendedWorkers = Number.isInteger(parallel.recommendedWorkers) ? parallel.recommendedWorkers : 1;
const parallelSummary = parallel.mode
  ? `; ParallelMode=${parallel.mode}; RecommendedWorkers=${recommendedWorkers}; ParallelSafeTests=${parallel.parallelSafeTests || 0}; SerialTests=${parallel.serialTests || 0}`
  : '; ParallelMode=legacy_serial; RecommendedWorkers=1; ParallelSafeTests=0; SerialTests=unknown';

process.stdout.write(
  `\`\`\`
@[/TEST SKILL 2 â€“ TEST RUN PRECHECK] Mode=TEST_RUN_PRECHECK; ExecutionModel=SWE_1_6; TestSpec=${args.spec}; TestPlan=${args.plan}; TargetTestRun=${plan.testRunId}; Capability=${capability}; Skill1Result=TEST_PLAN_CREATED; StrictValidator=TESTPLAN_VALID; GeneratorPlanTests=${plan.tests.length}${parallelSummary}; Rules=USE_ARTIFACTS_ONLY_VALIDATE_PRECHECK_NO_IMPLEMENTATION_NO_LIVE_TESTS; ExpectedOutput=READY_FOR_LIVE_TEST_OR_TEST_RUN_BLOCKED
\`\`\`
`,
);

