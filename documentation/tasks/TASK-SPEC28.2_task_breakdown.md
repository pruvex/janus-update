TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
- Task File: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
- Target Task: TASK-SPEC28.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 28 plus generated TASK-SPEC28 artifact; TASK-SPEC28.1 final audit and documentation update prove only the visible `LIVE_TEST_EXECUTION` gate and fail-closed entry behavior, while this released target task is the next bounded worker/auth/evidence contract slice and must not absorb TASK-SPEC28.3 accept/reject registry hardening
- Files: documentation/codex/skills/janus-test-pipeline/SKILL.md, documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py, documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py, documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py, documentation/codex/model-routing/strong-or-fixtures/, documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py
- Acceptance Criteria: a bounded local live-retest worker contract exists for only the allowed local health, chat creation, bound prompt execution, and evidence collection steps; local auth/header support is represented in a bounded, non-secret-leaking way; returned artifacts are reviewable by Codex and do not claim final PASS, release, Git, or routing authority; the contract cannot be reused as a generic live-test delegation or broad shell path
- Tests: extend focused runner and contract coverage for a valid local live-retest worker package; add a fixture-based contract check under `documentation/codex/model-routing/strong-or-fixtures/` or an adjacent scoped fixture path; run `python -m pytest documentation/codex/model-routing/tests/test_test_pipeline_sidecar_write_pilot_runner.py -q`; run `python -m py_compile documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py documentation/codex/model-routing/scripts/isolated_aider_workspace_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`; run a focused fixture/package validation command that proves secrets are not serialized and the worker package stays allowlisted; run `git diff --check` on the touched skill, script, fixture, and test artifacts
- Execution Model: 5.4
- Readiness: Scope is intentionally limited to the worker/auth/evidence contract needed after the visible gate. This target task may define and validate the bounded package shape and reviewable evidence output, but must not perform a real live retest, must not mark OR execution generally productive, must not grant final Codex-owned accept/reject semantics, and must not update registry or summary artifacts beyond the contract evidence needed for this slice.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

@janus-preimplementation-check
Spec: documentation/SPEC/28_bounded_or_lane_fuer_live_test_execution.md
Task: documentation/tasks/TASK-SPEC28_bounded_or_lane_fuer_live_test_execution.md
Backlog Item: BACKLOG-118
Target Task: TASK-SPEC28.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
