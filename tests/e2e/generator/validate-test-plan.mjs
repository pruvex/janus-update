#!/usr/bin/env node
/**
 * Deterministic Janus TestPlan validator.
 *
 * Usage:
 *   node tests/e2e/generator/validate-test-plan.mjs --plan documentation/test-runs/TEST-RUN-YYYY-MM-DD-NNN_plan.json
 *
 * This is intentionally stricter than generate-live-runner.mjs for pipeline
 * prechecks: it rejects meta-plan summary fields that are valid JSON but not a
 * generator-ready TestPlan.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    if (argv[i] === '--plan') args.plan = argv[i + 1];
  }
  return args;
}

function fail(errors) {
  console.error('TESTPLAN INVALID:');
  for (const error of errors) console.error(`  - ${error}`);
  process.exit(1);
}

function validate(plan, registry) {
  const errors = [];
  const requiredTop = [
    'testRunId',
    'title',
    'executionMode',
    'target',
    'chatWindow',
    'baseUrl',
    'backendHealthUrl',
    'timeouts',
    'strategies',
    'tests',
  ];
  const allowedTop = new Set(requiredTop);
  allowedTop.add('parallelization');
  const forbiddenMetaTop = [
    'schemaVersion',
    'capabilityName',
    'testObjective',
    'inputTestSpecPath',
    'testSpecPath',
    'testSpecName',
    'testspec_path',
    'testspec_name',
    'capability_name',
    'test_objective',
    'createdAt',
    'created_at',
    'created_by',
    'execution_model',
    'status',
    'config',
    'scope',
    'outOfScope',
    'securityGate',
    'security_gate',
    'securityScope',
    'security_risk',
    'ports',
    'janus_config',
    'providers',
    'providerMatrix',
    'providerModelMatrix',
    'provider_model_matrix',
    'testCases',
    'functionalTestCases',
    'functional_test_cases',
    'intentTestCases',
    'intent_test_cases',
    'naturalLanguageIntentCases',
    'securityTestCases',
    'security_test_cases',
    'promptInjectionTestCases',
    'prompt_injection_test_cases',
    'liveTestCases',
    'live_test_cases',
    'acceptanceCriteria',
    'acceptance_criteria',
    'blockingConditions',
    'blocking_conditions',
    'retestRules',
    'retest_rules',
    'costOptimization',
    'resultSchema',
    'resultMarkdownPath',
    'resultJsonPath',
    'requiredResultMarkdown',
    'requiredResultJson',
    'dashboardConsumption',
    'result_paths',
    'testspec_metadata',
    'metadata',
    'janus_ports',
    'testData',
    'test_data_and_sandbox',
    'testDataAndSandbox',
    'loggingAndTelemetry',
    'logging_and_telemetry',
    'loggingAndTelemetryPrivacy',
    'costAndTokenOptimization',
    'machine_readable_result_contract',
    'machineReadableTestResultContract',
    'cost_and_token_optimization',
    'skill_tool_routing_checks',
    'skillToolRoutingChecks',
    'live_janus_test_cases',
    'capability_explanation_target',
    'capabilityExplanationTarget',
    'userExperienceContract',
    'internal_complexity_breakdown',
    'internalTestComplexityBreakdown',
    'testSpecReviewExecutionRouting',
    'complexity',
    'test_run_id',
  ];

  for (const field of requiredTop) {
    if (!(field in plan)) errors.push(`Missing required field: ${field}`);
  }

  for (const field of Object.keys(plan)) {
    if (!allowedTop.has(field)) errors.push(`Unexpected top-level field: ${field}`);
  }

  for (const field of forbiddenMetaTop) {
    if (field in plan) errors.push(`Forbidden meta-plan field: ${field}`);
  }

  if (!plan.testRunId || !/^TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}$/.test(plan.testRunId)) {
    errors.push(`Invalid testRunId format: ${plan.testRunId}`);
  }

  if (!['LIVE_VISUAL', 'HEADLESS', 'LIVE_RETEST'].includes(plan.executionMode)) {
    errors.push(`Invalid executionMode: ${plan.executionMode}`);
  }

  if (!['JANUS_CHAT', 'JANUS_DASHBOARD', 'JANUS_ELECTRON', 'JANUS_BROWSER_SECURITY'].includes(plan.target)) {
    errors.push(`Invalid target: ${plan.target}`);
  }

  if (!['A', 'B', 'C', 'D'].includes(plan.chatWindow)) {
    errors.push(`Invalid chatWindow: ${plan.chatWindow}`);
  }

  if (!plan.timeouts || typeof plan.timeouts.testCaseMs !== 'number') errors.push('Missing timeouts.testCaseMs');
  if (!plan.timeouts || typeof plan.timeouts.assistantResponseMs !== 'number') errors.push('Missing timeouts.assistantResponseMs');
  if (!plan.timeouts || typeof plan.timeouts.streamRequestMs !== 'number') errors.push('Missing timeouts.streamRequestMs');

  const strategies = plan.strategies || {};
  for (const type of ['send', 'wait', 'evidence', 'evaluate']) {
    const value = strategies[type];
    const available = Object.keys(registry.strategies[type] || {});
    if (!value) errors.push(`Missing strategy: strategies.${type}`);
    else if (!available.includes(value)) errors.push(`Unknown strategy "${value}" for type "${type}". Available: ${available.join(', ')}`);
  }

  if (!Array.isArray(plan.tests) || plan.tests.length === 0) {
    errors.push('tests must be a non-empty array');
  } else {
    const ids = new Set();
    for (const testCase of plan.tests) {
      const label = testCase && testCase.id ? testCase.id : '?';
      for (const field of ['id', 'name', 'type', 'provider', 'model', 'prompt', 'expected']) {
        if (!(field in testCase)) errors.push(`Test ${label} missing ${field}`);
      }
      if ('parallelSafe' in testCase && typeof testCase.parallelSafe !== 'boolean') {
        errors.push(`Test ${label} invalid parallelSafe: ${testCase.parallelSafe}`);
      }
      if ('testDataNamespace' in testCase && typeof testCase.testDataNamespace !== 'string') {
        errors.push(`Test ${label} invalid testDataNamespace`);
      }
      if (ids.has(testCase.id)) errors.push(`Duplicate test id: ${testCase.id}`);
      ids.add(testCase.id);
      if (!['functional', 'intent_routing', 'ux', 'security', 'prompt_injection', 'cost_token', 'manual_gate'].includes(testCase.type)) {
        errors.push(`Test ${label} invalid type: ${testCase.type}`);
      }
      if (!['GPT', 'Gemini', 'Any'].includes(testCase.provider)) {
        errors.push(`Test ${label} invalid provider: ${testCase.provider}`);
      }
    }
  }

  if (plan.parallelization) {
    const p = plan.parallelization;
    if (typeof p.enabled !== 'boolean') errors.push('parallelization.enabled must be boolean');
    if (!Number.isInteger(p.recommendedWorkers) || p.recommendedWorkers < 1 || p.recommendedWorkers > 4) {
      errors.push('parallelization.recommendedWorkers must be 1..4');
    }
    if (!['serial_only', 'mixed_parallel_and_serial', 'all_parallel_safe'].includes(p.mode)) {
      errors.push(`parallelization.mode invalid: ${p.mode}`);
    }
  }

  return errors;
}

const args = parseArgs(process.argv);
if (!args.plan) fail(['Usage: node tests/e2e/generator/validate-test-plan.mjs --plan <plan.json>']);
if (!fs.existsSync(args.plan)) fail([`Plan file not found: ${args.plan}`]);

let plan;
try {
  plan = JSON.parse(fs.readFileSync(args.plan, 'utf-8'));
} catch (error) {
  fail([`JSON parse error: ${error.message}`]);
}

const registry = JSON.parse(fs.readFileSync(path.join(__dirname, 'strategy-registry.json'), 'utf-8'));
const errors = validate(plan, registry);
if (errors.length > 0) fail(errors);

console.log('TESTPLAN VALID');
console.log(`  TestRun: ${plan.testRunId}`);
console.log(`  Tests:   ${plan.tests.length}`);
console.log(`  Strategies: send=${plan.strategies.send}, wait=${plan.strategies.wait}, evidence=${plan.strategies.evidence}, evaluate=${plan.strategies.evaluate}`);
if (plan.parallelization) {
  console.log(`  Parallel: mode=${plan.parallelization.mode}, recommendedWorkers=${plan.parallelization.recommendedWorkers}, parallelSafe=${plan.parallelization.parallelSafeTests}, serial=${plan.parallelization.serialTests}`);
}
