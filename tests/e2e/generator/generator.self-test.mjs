#!/usr/bin/env node
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const generatorDir = path.join(repoRoot, 'tests/e2e/generator');

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, relativePath), 'utf-8'));
}

function runNode(args) {
  return execFileSync(process.execPath, args, {
    cwd: repoRoot,
    encoding: 'utf-8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
}

function assertSameSet(label, left, right) {
  const missing = left.filter((value) => !right.includes(value));
  const extra = right.filter((value) => !left.includes(value));
  assert.deepEqual({ missing, extra }, { missing: [], extra: [] }, `${label} schema/registry mismatch`);
}

function assertSchemaRegistrySync() {
  const schema = readJson('tests/e2e/generator/test-plan.schema.json');
  const registry = readJson('tests/e2e/generator/strategy-registry.json');
  const strategyProps = schema.properties.strategies.properties;

  assertSameSet('send', Object.keys(registry.strategies.send), strategyProps.send.enum);
  assertSameSet('wait', Object.keys(registry.strategies.wait), strategyProps.wait.enum);
  assertSameSet('evidence', Object.keys(registry.strategies.evidence), strategyProps.evidence.enum);
  assertSameSet('evaluate', Object.keys(registry.strategies.evaluate), strategyProps.evaluate.enum);
  assertSameSet('modelSelection', Object.keys(registry.modelSelection), strategyProps.modelSelection.enum);

  const resultSchema = readJson('tests/e2e/generator/test-result.schema.json');
  assert.equal(resultSchema.properties.schemaVersion.enum[0], 'janus.test-result.v1');
}

function assertValidTestResultRecord(record) {
  assert.equal(record.schemaVersion, 'janus.test-result.v1');
  assert.match(record.testRunId, /^TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}$/);
  assert.ok(['PASS', 'FAIL', 'PARTIAL', 'BLOCKED', 'RUNNING'].includes(record.status), `invalid status: ${record.status}`);
  assert.equal(typeof record.summary.total, 'number');
  assert.equal(typeof record.summary.passed, 'number');
  assert.equal(typeof record.summary.failed, 'number');
  assert.equal(typeof record.summary.blocked, 'number');
  assert.equal(typeof record.summary.manualGateRequired, 'number');
  assert.equal(typeof record.artifacts.resultDirectory, 'string');
  assert.equal(typeof record.artifacts.resultJson, 'string');
  assert.ok(Array.isArray(record.artifacts.evidenceFiles));
  assert.ok(Array.isArray(record.results));
  for (const result of record.results) {
    assert.equal(typeof result.testCaseId, 'string');
    assert.equal(typeof result.result, 'string');
    assert.equal(typeof result.classification, 'string');
    assert.equal(typeof result.evidencePath, 'string');
  }
  assert.equal(typeof record.updatedAt, 'string');
}

function assertSampleTestResultSchema() {
  assertValidTestResultRecord({
    schemaVersion: 'janus.test-result.v1',
    testRunId: 'TEST-RUN-2099-01-01-001',
    title: 'Sample',
    status: 'FAIL',
    summary: {
      total: 2,
      passed: 1,
      failed: 1,
      blocked: 0,
      manualGateRequired: 0,
    },
    artifacts: {
      resultDirectory: 'documentation/test-results/TEST-RUN-2099-01-01-001',
      resultJson: 'documentation/test-results/TEST-RUN-2099-01-01-001_results.json',
      evidenceFiles: ['documentation/test-results/TEST-RUN-2099-01-01-001/TC-001_evidence.json'],
    },
    results: [
      {
        testCaseId: 'TC-001',
        result: 'FAIL',
        classification: 'ASSERTION_MISMATCH',
        evidencePath: 'documentation/test-results/TEST-RUN-2099-01-01-001/TC-001_evidence.json',
        durationMs: 1200,
        notes: 'sample',
        timestamp: '2099-01-01T00:00:00.000Z',
      },
    ],
    updatedAt: '2099-01-01T00:00:00.000Z',
  });
}

function createSmokePlan(tmpDir) {
  const plan = {
    testRunId: 'TEST-RUN-2099-01-01-001',
    title: 'Generator Contract Smoke',
    executionMode: 'LIVE_VISUAL',
    target: 'JANUS_CHAT',
    chatWindow: 'A',
    baseUrl: 'http://127.0.0.1:5173',
    backendHealthUrl: 'http://127.0.0.1:8001/api/health',
    timeouts: {
      testCaseMs: 60000,
      assistantResponseMs: 45000,
      streamRequestMs: 10000,
    },
    strategies: {
      send: 'form_request_submit_v1',
      wait: 'assistant_stream_complete_v1',
      evidence: 'capture_network_v1',
      evaluate: 'tool_call_detected_v1',
      modelSelection: 'model_selection_v2_5',
    },
    tests: [
      {
        id: 'TC-GEN-001',
        name: 'Tool routing smoke',
        type: 'intent_routing',
        provider: 'GPT',
        model: 'gpt-5.4-mini',
        prompt: 'Nutze das Wetter-Tool fuer Berlin.',
        expected: {
          tool: 'system.weather',
          mustNotContain: ['ich kann das wetter nicht abrufen'],
        },
      },
    ],
  };
  const planPath = path.join(tmpDir, 'generator-smoke-plan.json');
  fs.writeFileSync(planPath, JSON.stringify(plan, null, 2));
  return planPath;
}

function assertGeneratedRunnerContract() {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'janus-generator-self-test-'));
  const planPath = createSmokePlan(tmpDir);
  const outPath = path.join(tmpDir, 'generator-smoke.live.spec.js');

  runNode(['tests/e2e/generator/generate-live-runner.mjs', '--plan', planPath, '--out', outPath]);
  runNode(['tests/e2e/generator/validate-runner.mjs', '--plan', planPath, '--runner', outPath]);
  runNode(['--check', outPath]);

  const runnerSrc = fs.readFileSync(outPath, 'utf-8');
  assert.match(runnerSrc, /writeTestResultSummary/);
  assert.match(runnerSrc, /TEST-RUN-2099-01-01-001_results\.json/);
  assert.match(runnerSrc, /janus\.test-result\.v1/);
  assert.match(runnerSrc, /form_request_submit_v1/);
  assert.match(runnerSrc, /model_selection_v2_5/);
  assert.doesNotMatch(runnerSrc, /test\.skip\(/);
}

function main() {
  assert.equal(fs.existsSync(path.join(generatorDir, 'generate-live-runner.mjs')), true);
  assertSchemaRegistrySync();
  assertSampleTestResultSchema();
  assertGeneratedRunnerContract();
  console.log('GENERATOR SELF-TEST PASSED');
}

main();
