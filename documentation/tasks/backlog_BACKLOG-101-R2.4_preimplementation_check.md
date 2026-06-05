PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-BACKLOG-101-R2.4
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-101_clean_deepdive_user_ux_and_cost_debug_log.md
Spec: documentation/SPEC/backlog_BACKLOG-101_deepdive_restore_cross_provider_cost_visibility_and_cache_savings.md
Backlog Item: BACKLOG-101
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: strengthen only the existing backend cost-tracking regression suite and the permanent DeepDive UI smoke so future changes cannot reintroduce forensic-first UX or leak user content into the debug log.
- Artifact identity is consistent across the approved `BACKLOG-101` Spec, the `TASK-BACKLOG-101-R2` task artifact, and the completed `TASK-BACKLOG-101-R2.1` through `TASK-BACKLOG-101-R2.3` execution results.
- Implementation risk is LOW to MEDIUM because this task should stay inside existing test surfaces and must not pull product logic or broad new E2E coverage into scope.
- A Git checkpoint is recommended through `janus-git-governance` before implementation because the worktree already contains the full BACKLOG-101 change chain and this task is the contract lock for that work.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_cost_token_tracking_completeness.py -q
- npx playwright test tests/e2e/generated/BACKLOG-101-ui-smoke.spec.js --headed --workers=1 --reporter=list
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
Reason: The regression guard is tightly bounded to two existing test surfaces and does not need high reasoning.
User Action: Say `ok` to start implementation of `TASK-BACKLOG-101-R2.4` with the bound scope and evidence gate above.
