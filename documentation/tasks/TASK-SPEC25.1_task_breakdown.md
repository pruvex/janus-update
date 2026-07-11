TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- Task File: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
- Target Task: TASK-SPEC25.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 25 plus generated TASK-SPEC25 artifact; the first productive OR main path must stay on one dedicated Dev-workhorse surface only, and older pilot families remain implementation context only and must not silently re-expand this first rollout
- Files: documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json, documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json, documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py, documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- Acceptance Criteria: the dedicated productive Dev-workhorse path allows only the explicitly pinned first bounded write/apply work classes; each allowed class has one fixed recommended OR model in the productive contract; missing class or model mapping blocks before any productive OR gate can appear; existing Spec-21, Spec-22, and Spec-23 paths outside the dedicated Dev-workhorse path remain unchanged
- Tests: add focused automated positive coverage for one allowed first productive work class with a valid fixed model mapping; add negative coverage that mixed review/assist-only classes are rejected inside the productive path; add negative coverage that missing fixed model mappings block before productive OR eligibility; add regression coverage that older pilot paths are not silently redefined; run focused eligibility tests plus scoped `git diff --check` on the touched config, helper, and test artifacts
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to the first productive class/model contract only. This slice must not change the visible operator gate, must not wire runtime execution, must not alter healthcheck closeout, and must not broaden the productive path beyond the first bounded write/apply classes. Its only job is to lock the first productive OR main-path contract so later slices can safely expose it and execute it.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

@janus-preimplementation-check
Spec: documentation/SPEC/25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Task: documentation/tasks/TASK-SPEC25_produktiver_dev_workhorse_hauptpfad_fuer_or_arbeitspferd.md
Backlog Item: N/A
Target Task: TASK-SPEC25.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
