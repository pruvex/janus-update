PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-BACKLOG-101-R2.1
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-101_clean_deepdive_user_ux_and_cost_debug_log.md
Spec: documentation/SPEC/backlog_BACKLOG-101_deepdive_restore_cross_provider_cost_visibility_and_cache_savings.md
Backlog Item: BACKLOG-101
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: reshape only the DeepDive backend/API contract so user-facing provider, model, savings, and compact truthfulness hints come first, without starting the debug-log or frontend tasks.
- Artifact identity is consistent across the approved `BACKLOG-101` Spec, the `TASK-BACKLOG-101-R2` task artifact, and the released target task `TASK-BACKLOG-101-R2.1`.
- Implementation risk is MEDIUM because the task changes a live cost-reporting contract used by the existing DeepDive flow, and a scope escape could blur the user/developer separation we just locked in.
- A Git checkpoint is recommended through `janus-git-governance` before implementation because the worktree already contains multiple documentation changes and this task affects a shared API contract.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m py_compile backend/data/crud.py backend/api/routers/system.py
- python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: Der Scope ist klar gebunden und riskant genug fuer saubere 5.4-Ausfuehrung, aber nicht komplex genug fuer high oder 5.5.
User Action: Say `ok` to start implementation of `TASK-BACKLOG-101-R2.1` with the bound scope and evidence gate above.
