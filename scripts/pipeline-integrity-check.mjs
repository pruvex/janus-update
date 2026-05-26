#!/usr/bin/env node
import { spawnSync } from 'node:child_process';

const steps = [
  {
    name: 'Generator self-test',
    command: process.execPath,
    args: ['tests/e2e/generator/generator.self-test.mjs'],
    cwd: process.cwd(),
  },
  {
    name: 'Generator syntax check',
    command: process.execPath,
    args: ['--check', 'tests/e2e/generator/generate-live-runner.mjs'],
    cwd: process.cwd(),
  },
  {
    name: 'Validator syntax check',
    command: process.execPath,
    args: ['--check', 'tests/e2e/generator/validate-runner.mjs'],
    cwd: process.cwd(),
  },
  {
    name: 'Dashboard API build',
    command: 'npm',
    args: ['run', 'build', '--workspace=@janus-dashboard/api'],
    cwd: 'janus-dashboard',
  },
  {
    name: 'Dashboard UI build',
    command: 'npm',
    args: ['run', 'build', '--workspace=@janus-dashboard/ui'],
    cwd: 'janus-dashboard',
  },
];

function runStep(step) {
  console.log(`\n[PIPELINE CHECK] ${step.name}`);
  const result = spawnSync(step.command, step.args, {
    cwd: step.cwd,
    stdio: 'inherit',
    shell: process.platform === 'win32',
  });

  if (result.status !== 0) {
    throw new Error(`${step.name} failed with exit code ${result.status}`);
  }
}

function main() {
  for (const step of steps) {
    runStep(step);
  }
  console.log('\nPIPELINE INTEGRITY CHECK PASSED');
}

main();
