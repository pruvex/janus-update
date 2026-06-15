PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC17.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC17_structured_executor_first_slice_for_or_sidecar_delegation.md
Spec: documentation/SPEC/17_structured_executor_first_slice_for_or_sidecar_delegation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: it implements only the structured action request intake and validation skeleton for one local executor entrypoint, without pulling generator mapping, validator mapping, dispatcher fallback integration, or write or apply authority from TASK-SPEC17.2 or TASK-SPEC17.3 into this slice.
- Artifact identity is consistent across Spec 17, the generated TASK-SPEC17 artifact, the released task-breakdown handoff `documentation/tasks/TASK-SPEC17.1_task_breakdown.md`, and the target task `TASK-SPEC17.1`.
- The affected file cluster is concrete and bounded to the existing executor surface: `documentation/codex/model-routing/scripts/codex_structured_action_executor.py`, `documentation/codex/model-routing/schemas/codex_delegated_action_request.schema.json`, fixture requests under `documentation/codex/model-routing/structured-action-fixtures/`, run artifacts under `documentation/codex/model-routing/structured-action-runs/`, and one focused executor test module to be added for request validation and deterministic rejection coverage.
- Implementation risk is MEDIUM because the slice is mechanically bounded but still sits on a sensitive delegation boundary where free shell behavior must remain forbidden and review artifacts must stay deterministic; a git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree already contains unrelated changes.
Affected Files:
- documentation/codex/model-routing/scripts/codex_structured_action_executor.py
- documentation/codex/model-routing/schemas/codex_delegated_action_request.schema.json
- documentation/codex/model-routing/structured-action-fixtures/
- documentation/codex/model-routing/structured-action-runs/
- documentation/codex/model-routing/tests/test_codex_structured_action_executor.py
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_executor.py
- python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_draft_markdown_2026-06-14.json
- python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json <new-invalid-request-fixture>
- pytest documentation/codex/model-routing/tests/test_codex_structured_action_executor.py -q
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_executor.py
- python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_draft_markdown_2026-06-14.json
- pytest documentation/codex/model-routing/tests/test_codex_structured_action_executor.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/17_structured_executor_first_slice_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC17_structured_executor_first_slice_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC17.1_task_breakdown.md
- documentation/codex/model-routing/scripts/codex_structured_action_executor.py
- documentation/codex/model-routing/schemas/codex_delegated_action_request.schema.json
Drop Context:
- old BACKLOG-110 contact-debug runtime history
- later TASK-SPEC17.2 and TASK-SPEC17.3 implementation details
- sidecar write-pilot and broad OR evaluation history that does not change the first executor skeleton requirements
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready, repo-local, and bounded to one deterministic executor skeleton that should land before any later mapping or dispatcher integration work.
User Action: Say `ok` to start implementation of `TASK-SPEC17.1` with the bound scope and evidence gate above.
