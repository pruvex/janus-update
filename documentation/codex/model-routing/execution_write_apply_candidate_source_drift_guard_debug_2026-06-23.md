SKILL 5 DEBUG RESULT: FIXED

Iteration: 2
Progress-Validierung: Failure Code RUNNER_ARTIFACT_MISMATCH; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- The delegated live write path still trusted an accepted source package based only on allowlist, diff, and validation artifacts, but it did not verify that the accepted patch basis still matched the current working tree before invoking the live sidecar write step.
- That left one gap between "accepted proposal-first package exists" and "package still targets the current repository shape", so stale accepted patches could reach the live write runner and only fail at apply time.
Fix Summary:
- Hardened `normalize_execution_patch_candidate_for_write_apply.py` so normalized write-apply source packages now carry `source_file_snapshots` for the accepted changed-file basis whenever those files exist in the current repository.
- Hardened `codex_execution_write_apply_candidate_runner.py` so live write validation requires those source snapshots and rejects the package before sidecar invocation when the current working tree has drifted from the accepted source basis.
- Added a focused live-path regression proving the sidecar is not invoked at all when the accepted source snapshot no longer matches the current file content.
Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m unittest documentation.codex.model-routing.tests.test_execution_write_apply_candidate_live_operator_path documentation.codex.model-routing.tests.test_normalize_execution_patch_candidate_for_write_apply documentation.codex.model-routing.tests.test_bounded_write_candidate_validation_acceptance`
  - `python -m py_compile documentation/codex/model-routing/scripts/normalize_execution_patch_candidate_for_write_apply.py documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py documentation/codex/model-routing/tests/test_execution_write_apply_candidate_live_operator_path.py documentation/codex/model-routing/tests/test_normalize_execution_patch_candidate_for_write_apply.py`
Artifact Identity Check: PASS
Final Feature Suite: PASS
Changed Files:
- `documentation/codex/model-routing/scripts/normalize_execution_patch_candidate_for_write_apply.py`
- `documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py`
- `documentation/codex/model-routing/tests/test_execution_write_apply_candidate_live_operator_path.py`
- `documentation/codex/model-routing/execution_write_apply_candidate_source_drift_guard_debug_2026-06-23.md`

NEXT_STEP
Target Skill: janus-executioner
Canonical State: HANDOFF
Required Artifacts:
- `documentation/codex/model-routing/execution_write_apply_candidate_source_drift_guard_debug_2026-06-23.md`
- `documentation/codex/model-routing/execution_write_apply_candidate_live_pilot_mismatch_debug_2026-06-23.md`
- `documentation/codex/model-routing/execution-review-fixtures/backlog_108_execution_patch_candidate_input_package_current_shape_2026-06-23.json`
- `backend/services/contact_manager.py`
- `backend/tools/memory_tools.py`
Evidence Paths:
- `documentation/codex/model-routing/scripts/normalize_execution_patch_candidate_for_write_apply.py`
- `documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py`
- `documentation/codex/model-routing/tests/test_execution_write_apply_candidate_live_operator_path.py`
- `documentation/codex/model-routing/execution_write_apply_candidate_source_drift_guard_debug_2026-06-23.md`
Failure Code:
- `RUNNER_ARTIFACT_MISMATCH`
Changed Files:
- `documentation/codex/model-routing/scripts/normalize_execution_patch_candidate_for_write_apply.py`
- `documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py`
- `documentation/codex/model-routing/tests/test_execution_write_apply_candidate_live_operator_path.py`
- `documentation/codex/model-routing/execution_write_apply_candidate_source_drift_guard_debug_2026-06-23.md`
Decision:
- The stale-source live write gap is now closed.
- Do not reuse `EXEC-WRITE-APPLY-SOURCE-BRIDGE-001` for another live write attempt against the current repository.
- Generate one fresh bounded `execution_patch_candidate` against the current local seam, then normalize that fresh accepted source before any later write-apply retry.
Reason:
- The next useful OR step is no longer more write-runner hardening. It is a fresh current-shape proposal-first run that can feed the now-hardened write/apply lane.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- Approve one fresh bounded `execution_patch_candidate` run for `BACKLOG-108` against the current repository shape.
