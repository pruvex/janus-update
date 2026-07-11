PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC25.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Spec: documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Backlog Item: N/A
Assigned Model: 5.4
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it introduces only the visible productive operator gate for the already sealed `TASK-SPEC25.1` class/model contract and must show the fixed recommended OR model plus the pre-call cost basis, estimated cost, and confidence before any wrapper or dispatcher path can start.
- Artifact identity is consistent across Spec 25, the generated `TASK-SPEC25` artifact, the released handoff `documentation/tasks/TASK-SPEC25.2_task_breakdown.md`, and target task `TASK-SPEC25.2`.
- The affected file cluster is concrete and bounded to the dedicated productive runner, the shared gate helper it may reuse, the focused runner tests, the budget-profile config that defines the cost basis source, and the Dev-environment runbook entry for the productive gate standard.
- Implementation risk is MEDIUM because this slice sits directly on the boundary between visible operator-gate UX and accidental scope drift into productive runtime execution. Skill 4 must reuse the sealed `TASK-SPEC25.1` class/model contract unchanged, must not pull forward delegated runtime execution, Codex-owned acceptance wiring, file-first capture, telemetry closeout, or healthcheck visibility, and must not imply a broad productive OR path for existing Janus skills outside the dedicated Dev-workhorse entry.
- This slice establishes only the pre-dispatch visible gate and its required prompt data. Productive bounded runtime execution belongs to `TASK-SPEC25.3`.
Affected Files:
- documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py
- documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py
- documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py
- documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json
- documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_codex_dev_workhorse_runner
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility
- git diff --check -- documentation/codex/model-routing/scripts/codex_dev_workhorse_runner.py documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py documentation/codex/model-routing/tests/test_codex_dev_workhorse_runner.py documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md
- one focused negative-path check that missing fixed model mapping, missing cost basis, missing estimated cost, or missing confidence aborts before wrapper or dispatcher invocation
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
- documentation/tasks/TASK-SPEC25.2_task_breakdown.md
- the exact runner, gate-helper, budget-profile, runbook, and focused test file cluster listed above
Drop Context:
- sealed `TASK-SPEC25.1` implementation details beyond the reused fixed class/model contract
- later productive runtime slice `TASK-SPEC25.3`
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
Reason: The visible productive gate slice is implementation-ready, tightly bounded to fixed-model display, cost-basis display, and pre-dispatch abort behavior, while productive runtime execution remains explicitly deferred.
User Action: Say `ok` to start implementation of `TASK-SPEC25.2` with the bound scope and evidence gate above.
