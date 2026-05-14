#!/usr/bin/env node
/**
 * Static validation script for generated Playwright live runners.
 *
 * Usage:
 *   node tests/e2e/generator/validate-runner.mjs \
 *     --plan documentation/test-runs/TEST-RUN-2026-05-11-005_plan.json \
 *     --runner tests/e2e/generated/TEST-RUN-2026-05-11-005.live.spec.js
 */

import fs from 'node:fs';

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i];
    const val = argv[i + 1];
    if (key === '--plan') args.plan = val;
    if (key === '--runner') args.runner = val;
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv);
  if (!args.plan || !args.runner) {
    console.error('Usage: node validate-runner.mjs --plan <plan.json> --runner <runner.spec.js>');
    process.exit(1);
  }

  const plan = JSON.parse(fs.readFileSync(args.plan, 'utf-8'));
  const runnerSrc = fs.readFileSync(args.runner, 'utf-8');
  const errors = [];

  // 1. Runner must mention testRunId
  if (!runnerSrc.includes(plan.testRunId)) {
    errors.push(`Runner does not contain testRunId: ${plan.testRunId}`);
  }

  // 2. Runner must mention all strategies
  for (const [type, name] of Object.entries(plan.strategies)) {
    if (!runnerSrc.includes(name)) {
      errors.push(`Runner does not mention strategy ${type}: ${name}`);
    }
  }

  // 3. Every test id must appear in runner
  for (const t of plan.tests) {
    if (!runnerSrc.includes(t.id)) {
      errors.push(`Runner missing test id: ${t.id}`);
    }
    if (!runnerSrc.includes(t.prompt.replace(/'/g, "\\'"))) {
      // Prompt may be truncated/escaped; this is a soft check
    }
  }

  // 4. Must NOT contain blocking sendMessage('A') import/await
  if (/await\s+sendMessage\s*\(\s*['"]A['"]\s*\)/.test(runnerSrc)) {
    errors.push('Runner contains blocking await sendMessage("A") — forbidden');
  }
  if (/import\s*\(\s*['"]\/js\/chat\.js['"]\s*\)/.test(runnerSrc)) {
    errors.push('Runner imports /js/chat.js directly — forbidden');
  }

  // 5. Must NOT contain test.skip
  if (/test\.skip\(/.test(runnerSrc)) {
    errors.push('Runner contains test.skip — forbidden');
  }

  // 6. Must contain evidence writer and buildEvidence
  if (!runnerSrc.includes('writeEvidence')) {
    errors.push('Runner missing writeEvidence function');
  }
  if (!runnerSrc.includes('buildEvidence')) {
    errors.push('Runner missing buildEvidence function');
  }

  // 7. Must contain error classifications
  const requiredClassifications = ['RUNNER_SELECTOR_FAILURE', 'RUNNER_WAIT_FAILURE', 'RUNNER_STREAM_TIMEOUT', 'FRONTEND_NOT_READY', 'BACKEND_HEALTH_FAIL', 'INFRASTRUCTURE_OFFLINE', 'PROVIDER_TIMEOUT', 'TOOL_ROUTING_FAILURE', 'ASSERTION_MISMATCH'];
  for (const cls of requiredClassifications) {
    if (!runnerSrc.includes(cls)) {
      errors.push(`Runner missing error classification: ${cls}`);
    }
  }

  if (!runnerSrc.includes('async function selectModel')) {
    errors.push('Runner missing selectModel helper');
  }
  if (!runnerSrc.includes('async function waitSendButtonReady')) {
    errors.push('Runner missing waitSendButtonReady helper');
  }
  if (!runnerSrc.includes('MODEL_PLAN_MAP')) {
    errors.push('Runner missing MODEL_PLAN_MAP');
  }
  if (!runnerSrc.includes(plan.strategies.modelSelection || 'model_selection_v1')) {
    errors.push(`Runner missing ${plan.strategies.modelSelection || 'model_selection_v1'} (evidence strategyVersions or registry marker)`);
  }

  // 8. Must contain stream request observation
  if (!runnerSrc.includes('/api/chat/stream')) {
    errors.push('Runner does not observe /api/chat/stream');
  }

  // 9. Must use real UI submit (Enter key, button click, or form requestSubmit)
  const hasEnterSubmit = runnerSrc.includes("press('Enter')");
  const hasButtonClick = runnerSrc.includes(".click()") && runnerSrc.includes("sendBtn");
  const hasFormSubmit = runnerSrc.includes("requestSubmit()") && runnerSrc.includes("chat-form");
  if (!hasEnterSubmit && !hasButtonClick && !hasFormSubmit) {
    errors.push('Runner does not use real UI submit (Enter, button click, or form requestSubmit)');
  }

  // 10. Must contain diagnostics
  if (!runnerSrc.includes('createPromptDiagnostics')) {
    errors.push('Runner missing createPromptDiagnostics');
  }

  // 11. Must use existing Janus helpers
  const requiredHelpers = ['loadJanusAppDataConfig', 'installInternalApiKeyRoute', 'createE2eJwt'];
  for (const h of requiredHelpers) {
    if (!runnerSrc.includes(h)) {
      errors.push(`Runner missing helper: ${h}`);
    }
  }

  if (errors.length > 0) {
    console.error('VALIDATION FAILED:');
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }

  console.log('VALIDATION PASSED');
  console.log(`  Plan:    ${args.plan}`);
  console.log(`  Runner:  ${args.runner}`);
  console.log(`  Tests:   ${plan.tests.length}`);
  console.log(`  Checks:  11`);
}

main();
