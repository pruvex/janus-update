# TEST-ARTIFACT SIDECAR LIVE RESULT

Canonical State: BLOCKED
Request: Run the first bounded `janus-test-pipeline` `workspace-write` Sidecar pilot for generated test artifacts only.

Bound Scope:

- TestSpec: `documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md`
- TEST_RUN_ID: `TEST-RUN-2026-06-14-901`
- Allowed outputs:
  - `documentation/test-runs/TEST-RUN-2026-06-14-901_plan.json`
  - `documentation/test-runs/TEST-RUN-2026-06-14-901_generated.spec.js`
  - `documentation/test-runs/TEST-RUN-2026-06-14-901_skill2_handover.txt`

Executed Checks:

- helper precheck dry-run: PASS
- live Sidecar runner invocation: TIMEOUT
- allowlist validation: PASS
- touched-file cap validation: PASS
- delete/rename/move tripwire: PASS
- output existence for `TEST-RUN-2026-06-14-901`: PASS for zero generated files, meaning no forbidden partial write remained

Evidence Paths:

- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-PRECHECK-001/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-001/summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-001/validation_summary.json`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-001/stderr.log`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-LIVE-001/stdout.log`

Root Cause:

- the delegated Sidecar process entered an infrastructure-only blocker before writing allowed artifacts
- inside the Sidecar shell, `node` was not resolvable by PATH
- the Sidecar then spent its time trying to discover Node and finally hit the runner timeout
- local operator shell verification shows the working Node binary exists at `C:\nvm4w\nodejs\node.exe`

Why This Is Not A Safety Failure:

- no out-of-scope file was touched
- no product code was changed
- no `documentation/test-results/*` file was created
- no partial generated output was left behind
- the allowlist and reject gates remained intact during the failed run

Decision:

- do not accept this run as delegated test-artifact evidence
- do not retry live in the same block
- prepare the next retry to use explicit `C:\nvm4w\nodejs\node.exe` invocation inside the bounded prompt instead of relying on `node` PATH resolution

Next Step:

- keep the pilot in `BLOCKED` state until one explicitly approved live retry is run with the full Node path baked into the generator command
