PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC17.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC17_structured_executor_first_slice_for_or_sidecar_delegation.md
Spec: documentation/SPEC/17_structured_executor_first_slice_for_or_sidecar_delegation.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: add exactly one deterministic `run_generator` mapping for the first bounded `janus-test-pipeline` path, enforce declared output artifacts for that generator, capture stdout or stderr plus exit code, and return a reviewable fallback status when the route is missing or the generator fails.
- Artifact identity is consistent across Spec 17, the generated TASK-SPEC17 artifact, and the completed `TASK-SPEC17.1` execution result. The implementation must build on the new action gate from 17.1 without reopening request-intake scope or pulling validator and dispatcher work from TASK-SPEC17.3 forward.
- There is one visible prototype drift to handle inside scope: the task artifact binds the first generator slice to `tests/e2e/generator/compile-testspec-to-testplan.mjs`, while the existing executor prototype and saved fixtures still reference `generate_live_runner_v1` plus `generate-live-runner.mjs`. The task may reconcile that mismatch only by converging on one explicit first generator route and matching fixtures or tests; it must not broaden into multi-generator support.
- Implementation risk is HIGH because the slice edits a sensitive delegation boundary and because the current executor file still contains deeper later-slice helper code. A git checkpoint is recommended through `janus-git-governance` before Skill 4 because the worktree already contains unrelated changes.
Affected Files:
- documentation/codex/model-routing/scripts/codex_structured_action_executor.py
- tests/e2e/generator/compile-testspec-to-testplan.mjs
- tests/e2e/generator/generate-live-runner.mjs
- documentation/codex/model-routing/structured-action-fixtures/
- documentation/codex/model-routing/tests/test_codex_structured_action_executor.py
Evidence Focus:
- python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_executor.py documentation/codex/model-routing/tests/test_codex_structured_action_executor.py
- python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json <task-bound-generator-request-fixture>
- python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json <unknown-generator-request-fixture>
- pytest documentation/codex/model-routing/tests/test_codex_structured_action_executor.py -q
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_executor.py documentation/codex/model-routing/tests/test_codex_structured_action_executor.py
- python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json <task-bound-generator-request-fixture>
- python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json <unknown-generator-request-fixture>
- pytest documentation/codex/model-routing/tests/test_codex_structured_action_executor.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/17_structured_executor_first_slice_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC17_structured_executor_first_slice_for_or_sidecar_delegation.md
- documentation/tasks/TASK-SPEC17.1_execution_result.md
- documentation/codex/model-routing/scripts/codex_structured_action_executor.py
- tests/e2e/generator/compile-testspec-to-testplan.mjs
- tests/e2e/generator/generate-live-runner.mjs
Drop Context:
- old BACKLOG-110 contact-debug runtime history
- validator-path and dispatcher-fallback work reserved for TASK-SPEC17.3
- broad sidecar, OR, and write-pilot history that does not change the first generator mapping decision
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready but needs careful in-scope reconciliation between the task-bound first generator route and the existing executor prototype without widening into validator or dispatcher work.
User Action: Say `ok` to start implementation of `TASK-SPEC17.2` with the bound scope and evidence gate above.
