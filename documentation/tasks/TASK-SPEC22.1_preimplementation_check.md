PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC22.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Spec: documentation/SPEC/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it defines the first dedicated `productive_dev_workhorse_path` boundary contract and hardens OR eligibility only for that new path, without creating the later operator runner, dispatcher wiring, acceptance logic, or telemetry flow.
- Artifact identity is consistent across Spec 22, the generated TASK-SPEC22 artifact, the released handoff `documentation/tasks/TASK-SPEC22.1_task_breakdown.md`, and target task `TASK-SPEC22.1`.
- The affected file cluster is concrete and bounded to the shared eligibility config, the OR task budget config, the shared eligibility helper, and focused eligibility regression tests.
- Implementation risk is HIGH because this slice defines the first productive OR boundary for Dev work. Skill 4 must keep the rollout on one dedicated path only, must not reopen existing Janus, Codex, Spec-21, Quickchange, Doku, or sidecar paths as productive OR entry points, and must not pull forward operator-runner, dispatcher-execution, acceptance, or telemetry scope from later Spec-22 slices. A git checkpoint is recommended through `janus-git-governance` before Skill 4 if the broader worktree remains mixed.
- This slice establishes only the path contract, allowed bounded task classes, and deterministic pre-gate blocking for out-of-path, out-of-class, or missing-prerequisite cases. Any visible `1 = Codex / 2 = OR` gate remains reserved for `TASK-SPEC22.2`.
Affected Files:
- documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json
- documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
Evidence Focus:
- focused automated positive coverage for an in-scope `productive_dev_workhorse_path` request
- focused negative coverage that existing workflows outside the new path stay Codex-only
- focused negative coverage that non-allowed task classes inside the new path are rejected
- focused negative coverage that missing budget or estimate prerequisites block before OR eligibility
- python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation/tasks/TASK-SPEC22.1_preimplementation_check.md
- git diff --check -- documentation/tasks/TASK-SPEC22.1_preimplementation_check.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- focused eligibility helper and config regression tests for the touched file cluster
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
- documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
- documentation/tasks/TASK-SPEC22.1_task_breakdown.md
- the exact config, helper, and test file cluster listed above
Drop Context:
- later Spec-22 slices for the operator runner, delegated execution, acceptance, and telemetry
- unrelated Spec-21 pilot internals beyond the fact that they must not gain new productive entry points here
- unrelated quickchange, direct OR, doc-skill OR, sidecar write, or Janus product-routing history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The first Spec-22 slice is implementation-ready and tightly scoped to the dedicated Dev-workhorse boundary contract, allowed task classes, and deterministic pre-gate blocking, while keeping runner, acceptance, and telemetry work for later slices.
User Action: Say `ok` to start implementation of `TASK-SPEC22.1` with the bound scope and evidence gate above.
