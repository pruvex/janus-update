PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: TASK-SPEC29.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
Spec: documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: establish the hidden candidate lifecycle for silent routine learning in v1 by adding an internal candidate state, enforcing fail-closed suitability guards, and applying the fixed 30-day expiry rule.
- The slice is persistence- and backend-only. It must not create visible saved routines, passive chat storage/use hints, settings management, or any user-facing routine administration surface.
- The main acceptance path is one qualifying successful multi-step workflow that creates exactly one internal candidate, while risky, sensitive, strongly context-dependent, unstable, or otherwise ineligible flows create none.
- Risk is MEDIUM because the slice touches data model and workflow persistence behavior, but scope remains bounded to one internal lifecycle slice without UI or transport expansion.
Affected Files:
- backend/data/models.py
- backend/data/database.py
- backend/services/workflow/workflow_detector.py
- backend/services/workflow/step_trace_extractor.py
- backend/services/workflow/routine_store.py
- backend/tests/test_workflow_detector.py
- backend/tests/test_routine_store.py
- documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29.1_task_breakdown.md
- documentation/tasks/TASK-SPEC29.1_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Evidence Focus:
- python -m pytest backend/tests/test_workflow_detector.py -v
- python -m pytest backend/tests/test_routine_store.py -v
- python -m py_compile backend/data/models.py backend/data/database.py backend/services/workflow/workflow_detector.py backend/services/workflow/step_trace_extractor.py backend/services/workflow/routine_store.py
- git diff --check -- backend/data/models.py backend/data/database.py backend/services/workflow/workflow_detector.py backend/services/workflow/step_trace_extractor.py backend/services/workflow/routine_store.py backend/tests/test_workflow_detector.py backend/tests/test_routine_store.py documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md documentation/tasks/TASK-SPEC29.1_task_breakdown.md documentation/tasks/TASK-SPEC29.1_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not add automatic promotion, passive chat transparency, settings UI, routines API, OAuth, transport changes, or any visible routine-management behavior in this slice.
- Cursor-first should be checked again at execution time for this bounded write-capable slice when the shared execution gate exposes a sensible Cursor lane; Codex remains owner of review, validation, and final state.
Automated Evidence Gate:
- python -m pytest backend/tests/test_workflow_detector.py -v
- python -m pytest backend/tests/test_routine_store.py -v
- python -m py_compile backend/data/models.py backend/data/database.py backend/services/workflow/workflow_detector.py backend/services/workflow/step_trace_extractor.py backend/services/workflow/routine_store.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29.1_task_breakdown.md
- documentation/tasks/TASK-SPEC29.1_preimplementation_check.md
- backend/data/models.py
- backend/data/database.py
- backend/services/workflow/workflow_detector.py
- backend/services/workflow/step_trace_extractor.py
- backend/services/workflow/routine_store.py
- backend/tests/test_workflow_detector.py
- backend/tests/test_routine_store.py
Drop Context:
- later TASK-SPEC29.2 automatic promotion and passive chat transparency work
- later TASK-SPEC29.3 settings management and routines API work
- old unrelated workflow debug history and unrelated dirty worktree changes
- broader autonomous learning ideas outside the approved v1 routine scope
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: TASK-SPEC29.1 is now a bounded backend-and-persistence implementation slice with explicit files, tests, and fail-closed scope.
User Action: Continue with janus-executioner for `TASK-SPEC29.1`, and probe the shared execution gate for a sensible Cursor-first write-capable lane before local implementation.
