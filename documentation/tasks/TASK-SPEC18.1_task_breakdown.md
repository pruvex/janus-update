TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- Task File: documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- Target Task: TASK-SPEC18.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: reviewed Spec 18 plus generated TASK-SPEC18 artifact; older sidecar live runs, broad structured-action fixture folders, and historical OR evaluation artifacts remain implementation context only and must not widen the first write-candidate gate slice
- Files: documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py, documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py, documentation/codex/model-routing/structured-action-fixtures/, documentation/codex/model-routing/tests/
- Acceptance Criteria: exact target-task contract enforced; missing allowlist rejected; missing touched-file cap rejected; delete-rename-move intent rejected; reviewable reject or fallback status emitted before later diff or validation phases
- Tests: python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py; add one bounded write-candidate fixture with exact allowlist and touched-file cap and one invalid fixture per blocked entry condition; run focused pytest coverage for missing allowlist, missing touched-file cap, and delete-rename-move tripwire behavior
- Execution Model: 5.4
- Readiness: Scope is bounded to the delegated write-candidate entry gate only: enforce one exact prechecked target-task contract, require exact editable-path allowlist and touched-file cap, reject delete-rename-move intent, and emit reviewable reject or fallback status before any later diff-capture or validation-summary expansion. Diff capture, changed-files capture, validation-summary capture, and Codex-owned accept-reject normalization remain out of scope for this first target task.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

@janus-preimplementation-check
Spec: documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
Task: documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
Backlog Item: N/A
Target Task: TASK-SPEC18.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
