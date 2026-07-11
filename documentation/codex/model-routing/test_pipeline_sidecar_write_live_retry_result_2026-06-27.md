# TEST-ARTIFACT SIDECAR LIVE RETRY RESULT

Canonical State: BLOCKED
Date: `2026-06-27`
Skill Surface: `janus-test-pipeline`
Mode: `TESTSPEC_TO_TEST_PLAN`
Workflow ID: `SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-124`

## Bound Scope

- TestSpec: `documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md`
- TEST_RUN_ID: `TEST-RUN-2026-06-27-124`
- Allowed outputs:
  - `documentation/test-runs/TEST-RUN-2026-06-27-124_plan.json`
  - `documentation/test-runs/TEST-RUN-2026-06-27-124_generated.spec.js`
  - `documentation/test-runs/TEST-RUN-2026-06-27-124_skill2_handover.txt`

## Executed Checks

- bounded live pilot runner invocation: PASS at wrapper level
- allowlist validation: PASS
- touched-file cap validation: PASS
- delete/rename/move tripwire: PASS
- local post-validation of generated outputs: FAIL
- local direct generator seam with the same explicit `--test-run-id`: PASS outside the delegated sidecar runtime

## Observed Result

- the delegated wrapper completed with `status=PASS` and `artifact_success=true`
- the delegated run produced no allowed output artifacts
- the delegated last message claimed the exact full-path Node command failed immediately because `C:\nvm4w\nodejs\node.exe` was not found
- the local host environment disproves that claim:
  - `Test-Path C:\nvm4w\nodejs\node.exe`: `True`
  - direct local command `C:\nvm4w\nodejs\node.exe tests/e2e/generator/compile-testspec-to-testplan.mjs --spec ... --test-run-id TEST-RUN-2026-06-27-124`: PASS

## Stronger Root Cause

This is no longer a generator-contract blocker and no longer a missing `--test-run-id` blocker.

The remaining blocker is the delegated runtime path itself:

- `stderr.log` shows a Windows sandbox execution failure:
  - `windows sandbox: CreateProcessWithLogonW failed: 1056`
- this occurred while the delegated Codex sidecar tried to execute internal PowerShell reads for skill loading
- the delegated path therefore never reached a trustworthy generator execution step inside the bounded `workspace-write` runtime
- the last message's `node.exe not found` explanation is not reliable as the primary root cause because the same path works locally outside the sidecar runtime

## Why This Still Matters

The repaired pilot helper is still useful and now proves two real things:

- the bounded prompt and command contract are now correct
- the target generator path is locally valid for the exact requested `TEST_RUN_ID`

What remains red is the Windows delegated `workspace-write` runtime/tool-exec seam, not the test-artifact contract itself.

## Decision

- do not accept this run as successful delegated test-artifact evidence
- do not classify the generator path as blocked
- treat the next step as sidecar runtime hardening or alternate bounded worker execution, not another blind retry of the same live path

## Evidence Paths

- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-124/summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-124/validation_summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-124/post_validation_summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-124/stderr.log`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-2026-06-27-124/last_message.md`

## Recommended Next Step

- debug or replace the delegated Windows `workspace-write` execution seam before spending more live attempts on this exact sidecar path
