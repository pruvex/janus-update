# TEST-ARTIFACT SIDECAR LIVE RETRY RESULT

Canonical State: BLOCKED
Request: Run one hardened retry of the bounded `janus-test-pipeline` `workspace-write` Sidecar pilot after the original PATH-based Node resolution failure.

Bound Scope:

- TestSpec: `documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md`
- TEST_RUN_ID: `TEST-RUN-2026-06-14-901`
- Allowed outputs:
  - `documentation/test-runs/TEST-RUN-2026-06-14-901_plan.json`
  - `documentation/test-runs/TEST-RUN-2026-06-14-901_generated.spec.js`
  - `documentation/test-runs/TEST-RUN-2026-06-14-901_skill2_handover.txt`

Executed Checks:

- helper precheck dry-run: PASS
- live Sidecar runner invocation: PASS at wrapper level
- allowlist validation: PASS
- touched-file cap validation: PASS
- delete/rename/move tripwire: PASS
- post-run artifact existence: FAIL
- local post-validation of plan/runner outputs: FAIL because the expected files were never created

Evidence Paths:

- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-RETRY-PRECHECK-001/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-RETRY-001/summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-RETRY-001/validation_summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-RETRY-001/post_validation_summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-RETRY-001/last_message.md`

Observed Behavior:

- the Sidecar did not write any out-of-scope files
- the Sidecar also did not create any of the three allowed target files
- the Sidecar summary text shows the exact command still failed immediately in PowerShell:
  - `Die Benennung "C:\nvm4w\nodejs\node.exe" wurde nicht als Name eines Cmdlet ... erkannt.`

Likely Root Cause:

- the original blocker changed from `node` PATH discovery to Windows command invocation syntax
- the explicit binary path was passed as plain text, but not in a PowerShell-safe invoked form
- the next retry should use:
  - `& "C:\nvm4w\nodejs\node.exe" "tests/e2e/generator/compile-testspec-to-testplan.mjs" --spec "documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md"`

Why This Is Still A Safe Failure:

- no product code was touched
- no `documentation/test-results/*` file was created
- no partial or malformed target artifacts were left behind
- all write-scope tripwires remained intact

Decision:

- do not accept this retry as delegated test-artifact evidence
- keep the class in `BLOCKED` state
- treat the next step as one narrower shell-invocation fix, not a content-quality issue
