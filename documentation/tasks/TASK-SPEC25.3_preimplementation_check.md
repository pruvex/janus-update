PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC25.3
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Spec: documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Backlog Item: N/A
Assigned Model: 5.4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it wires only the productive bounded runtime for the already sealed Dev-workhorse path and must reuse the sealed `TASK-SPEC25.1` class/model contract and the sealed `TASK-SPEC25.2` visible operator gate unchanged.
- Artifact identity is consistent across Spec 25, the generated `TASK-SPEC25` artifact, the released handoff `documentation/tasks/TASK-SPEC25.3_task_breakdown.md`, and target task `TASK-SPEC25.3`.
- The affected file cluster is concrete and bounded to the dedicated productive runner, the shared bounded delegation dispatcher, the two bounded execution candidate runners, and the focused runner regression module for the productive path.
- Implementation risk is HIGH because this slice sits directly on the trust boundary between visible OR selection and real bounded delegated write/apply execution. Skill 4 must not alter fixed model mapping, visible cost-basis gate behavior, production-routing semantics, canonical routing-table state, or broad OR activation outside the two allowlisted productive classes.
- This slice must end in explicit Codex-owned `accept`, `reject`, `fallback`, or `manual review` outcomes with visible file-first artifacts and local validation. It must not treat delegated output as self-authenticating success.
Affected Files:
- documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py
- documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py
- documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner
- python -m py_compile documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
- git diff --check -- documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
- one focused negative-path check that unsupported classes, scope escapes, weak delegated outcomes, or local validation failures end deterministically in Codex-owned non-accept states
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
- documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- documentation/tasks/TASK-SPEC25.3_task_breakdown.md
- the exact productive runner, bounded dispatcher, execution candidate runner, and focused test file cluster listed above
Drop Context:
- sealed `TASK-SPEC25.1` implementation details beyond the reused class/model contract
- sealed `TASK-SPEC25.2` implementation details beyond the reused visible gate and cost-basis boundary
- older pilot families from Specs 21 to 24 except where they remain regression boundaries
- unrelated direct-OR, sidecar, quickchange, debug-consumer, or contact-memory history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The productive bounded runtime slice is implementation-ready, tightly bounded to the two allowlisted write/apply classes, the existing visible gate, file-first artifacts, local validation, and explicit Codex-owned completion states.
User Action: Say `ok` to start implementation of `TASK-SPEC25.3` with the bound scope and evidence gate above.
