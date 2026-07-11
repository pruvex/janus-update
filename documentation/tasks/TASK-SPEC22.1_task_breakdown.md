TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
- Task File: documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
- Target Task: TASK-SPEC22.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 22 plus generated TASK-SPEC22 artifact; the first rollout must stay on one dedicated Dev-workhorse path only, and existing Janus, Codex, Spec-21, Quickchange, Doku, and sidecar paths remain implementation context only and must not gain implicit productive OR entry through this slice
- Files: documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json, documentation/codex/model-routing/config/or_task_budget_profiles_2026-06-19.json, documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py, documentation/codex/model-routing/tests/test_bounded_or_worker_eligibility.py
- Acceptance Criteria: a new dedicated `productive_dev_workhorse_path` eligibility contract exists and is locally testable; only `test_result_triage_review`, `execution_patch_candidate`, and `execution_write_apply_candidate` can become OR-eligible inside this new path; existing Janus and Codex workflows outside this path stay deterministically Codex-only; missing path, budget, or estimate prerequisites block before any OR gate can be offered
- Tests: add focused automated positive coverage for an in-scope `productive_dev_workhorse_path` request; add negative coverage that existing workflows outside the path stay Codex-only; add negative coverage that non-allowed task classes inside the new path are rejected; add negative coverage that missing budget or estimate prerequisites block before OR eligibility; run focused eligibility tests plus scoped `git diff --check` on the touched config, helper, and test artifacts
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to the path contract and eligibility boundary only. This slice must not create the new operator runner, must not wire dispatcher execution, must not add file-first telemetry, and must not reopen existing skill-native productive OR entry points. Its only job is to define and harden the first dedicated productive Dev-workhorse boundary so later slices can build on one deterministic gate.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

@janus-preimplementation-check
Spec: documentation/SPEC/22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Task: documentation/tasks/TASK-SPEC22_operator_gesteuerter_or_arbeitspferd_produktivmodus_fuer_dev_arbeit.md
Backlog Item: N/A
Target Task: TASK-SPEC22.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
