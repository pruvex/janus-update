PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC18.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
Spec: documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it implements only the delegated write-candidate entry gate for one exact prechecked target-task contract, exact editable-path allowlist requirement, touched-file-cap requirement, delete-rename-move tripwire, and reviewable reject or fallback status before any later diff-capture or validation-summary phases.
- Artifact identity is consistent across reviewed Spec 18, the generated TASK-SPEC18 artifact, the released task-breakdown handoff `documentation/tasks/TASK-SPEC18.1_task_breakdown.md`, and the target task `TASK-SPEC18.1`.
- The affected file cluster is concrete and bounded to the delegated entry-gate surface: `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`, `documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py`, one narrow fixture family under `documentation/codex/model-routing/structured-action-fixtures/`, and one focused bounded-delegation test module under `documentation/codex/model-routing/tests/`.
- Implementation risk is MEDIUM because the slice is mechanically narrow but sits on a sensitive write-boundary seam where allowlist drift, touched-file-cap drift, or hidden delete-rename-move behavior would weaken later delegated write safety. A git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree still contains unrelated dirt outside this bounded slice.
Affected Files:
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py
- documentation/codex/model-routing/structured-action-fixtures/
- documentation/codex/model-routing/tests/
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py
- pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py -q
- fixture-based local reject-path checks for missing allowlist, missing touched-file cap, and delete-rename-move tripwire
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py
- pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC18.1_task_breakdown.md
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py
Drop Context:
- later TASK-SPEC18.2 diff-capture details
- later TASK-SPEC18.3 validation-summary and accept-reject details
- broad sidecar live-run history and OR evaluation artifacts that do not change the first entry-gate requirements
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, repo-local, and bounded to one exact delegated write-candidate entry gate before any later diff or validation expansion work.
User Action: Say `ok` to start implementation of `TASK-SPEC18.1` with the bound scope and evidence gate above.
