PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC25.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Spec: documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_PRECHECK
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it only pins the first productive Dev-workhorse work classes and their fixed recommended OR models inside the dedicated productive path contract.
- Artifact identity is consistent across Spec 25, the generated `TASK-SPEC25` artifact, and the released `TASK-SPEC25.1` breakdown handoff. No product-facing Janus feature path or legacy pilot artifact is the source of truth for this slice.
- The affected file cluster is concrete and bounded to the productive-path eligibility contract, the budget-profile config, the shared eligibility helper, and the focused eligibility regression tests.
- Risk is MEDIUM because this slice hardens the first productive OR main-path contract and can accidentally reopen broader pilot scope if handled loosely. Skill 4 must preserve the hard boundary: no operator-gate output changes, no runtime wiring, no dispatcher execution changes, no healthcheck closeout changes, and no broadening beyond the first bounded write/apply classes.
- This slice is contract-only for the productive main path. It may pin the first allowed classes and fixed recommended OR models, but it must not yet expose those models in the visible gate and must not execute the productive runtime path.
Affected Files:
- documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json
- documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
Evidence Focus:
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility
- python -m py_compile documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- git diff --check -- documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py documentation/tasks/TASK-SPEC25.1_preimplementation_check.md
- one focused negative-path check that older mixed review/assist-only pilot classes do not become productive main-path classes
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m unittest documentation.codex.model-routing.tests.test_bounded_or_worker_eligibility
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- documentation/tasks/TASK-SPEC25.1_task_breakdown.md
- documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json
- documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json
- documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py
- documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
Drop Context:
- visible operator-gate work reserved for TASK-SPEC25.2
- productive runtime wiring reserved for TASK-SPEC25.3
- old direct-OR, sidecar, and broad pilot history beyond the already accepted contract context
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The first productive Dev-workhorse class/model contract is implementation-ready, tightly bounded to config and eligibility hardening only, and explicitly fenced away from visible gate or runtime execution work.
User Action: Say `ok` to start implementation of `TASK-SPEC25.1` with the bound scope and evidence gate above.
