PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC22.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Spec: documentation/SPEC/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Backlog Item: N/A
Assigned Model: 5.4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it introduces only the dedicated visible operator entry for the already sealed `productive_dev_workhorse_path` and requires a clear `1 = Codex` / `2 = OR` choice with selected model, estimated cost, confidence, and scope hints before any delegation path can begin.
- Artifact identity is consistent across Spec 22, the generated `TASK-SPEC22` artifact, the released handoff `documentation/tasks/TASK-SPEC22.2_task_breakdown.md`, and target task `TASK-SPEC22.2`.
- The affected file cluster is concrete and bounded to the new dedicated runner, the shared gate helper it may reuse, the focused runner plus eligibility regression tests, and the Dev-environment runbook entry for the new productive path.
- Implementation risk is MEDIUM because this slice sits on the boundary between safe visible operator UX and accidental scope drift into delegated runtime behavior. Skill 4 must reuse the sealed `TASK-SPEC22.1` eligibility contract unchanged, must not pull forward dispatcher mapping, Codex-owned acceptance, actual-cost closeout, or healthcheck ingestion, and must not imply a broad productive OR path for existing Janus skills outside the dedicated Dev-workhorse entry.
- This slice establishes only the pre-dispatch operator entry and mandatory prompt data. Delegated execution wiring belongs to `TASK-SPEC22.3`, and telemetry plus actual-cost closeout belong to `TASK-SPEC22.4`.
Affected Files:
- documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
- documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
- documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility
- git diff --check -- documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- one focused negative-path check that missing estimated cost, missing confidence, or failed eligibility aborts before wrapper or dispatcher invocation
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
- documentation/tasks/TASK-SPEC22.2_task_breakdown.md
- the exact runner, gate-helper, runbook, and focused test file cluster listed above
Drop Context:
- sealed boundary-contract implementation details beyond the reused `TASK-SPEC22.1` allowlist and fail-closed estimate gate
- later delegated execution slice `TASK-SPEC22.3`
- later telemetry and healthcheck slice `TASK-SPEC22.4`
- unrelated direct-OR, sidecar, quickchange, or contact-memory history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The visible Dev-workhorse entry slice is implementation-ready, tightly bounded to prompt-mode operator gating, mandatory estimate/confidence display, and pre-dispatch abort behavior, while delegated runtime and telemetry remain explicitly deferred.
User Action: Say `ok` to start implementation of `TASK-SPEC22.2` with the bound scope and evidence gate above.
