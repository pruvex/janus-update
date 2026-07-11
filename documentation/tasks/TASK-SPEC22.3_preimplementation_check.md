PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC22.3
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Spec: documentation/SPEC/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Backlog Item: N/A
Assigned Model: 5.4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it wires the already sealed visible Dev-workhorse gate into real bounded delegated runtime for exactly three allowlisted classes and keeps Codex as the explicit final owner of acceptance, rejection, fallback, or manual review.
- Artifact identity is consistent across Spec 22, the generated `TASK-SPEC22` artifact, the released handoff `documentation/tasks/TASK-SPEC22.3_task_breakdown.md`, and target task `TASK-SPEC22.3`.
- The affected file cluster is concrete and bounded to the dedicated runner, the shared local delegation dispatcher, the three already existing bounded delegation consumers, and focused regression coverage on the dedicated Dev-workhorse runtime path.
- Implementation risk is MEDIUM because this slice enables real delegation and therefore sits on the seam between operator choice and local acceptance authority. Skill 4 must reuse the sealed `TASK-SPEC22.1` productive-path boundary unchanged, must preserve the sealed `TASK-SPEC22.2` visible gate semantics, and must not pull forward actual-cost closeout, session telemetry persistence, or healthcheck ingestion from `TASK-SPEC22.4`.
- This slice establishes only the real delegated runtime and Codex-owned outcome normalization for the three allowlisted classes. Actual-cost visibility, file-first telemetry, and healthcheck visibility remain deferred to `TASK-SPEC22.4`.
Affected Files:
- documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py
- documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py
- documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py
- documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner
- python -m unittest documentation.codex.model-routing.tests.test_assistive_or_review_capture_dispatcher
- python -m unittest documentation.codex.model-routing.tests.test_quickchange_live_operator_path
- git diff --check -- documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
- one focused negative-path check that unsupported task classes, rejected delegated outcomes, or scope-escaping results terminate as deterministic fallback or manual-review states
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m unittest documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
- documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
- documentation/tasks/TASK-SPEC22.3_task_breakdown.md
- the exact runner, dispatcher, bounded delegation consumer scripts, and focused runtime regression cluster listed above
Drop Context:
- closed documentation-sync chatter for `TASK-SPEC22.2`
- later telemetry and actual-cost closeout slice `TASK-SPEC22.4`
- unrelated direct-OR, sidecar, janus-quickchange, or contact-memory history outside the bounded runtime seam
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The bounded delegated Dev-workhorse runtime slice is implementation-ready, tightly scoped to three allowlisted classes plus explicit Codex-owned accept-or-reject outcomes, while actual-cost closeout and telemetry remain deferred.
User Action: Say `ok` to start implementation of `TASK-SPEC22.3` with the bound scope and evidence gate above.
