PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: TASK-SPEC29.2
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
Spec: documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: wire second-hit candidate matching into automatic promotion and replace the old explicit save-offer interruption with passive transparency only for the in-scope silent-learning path.
- The first qualifying case must stay completely silent. No passive storage hint may appear on first creation of a hidden candidate, and the old `JANUS_ROUTINE_OFFER` marker plus visible save question must not be emitted for this path.
- Passive user-visible messaging may appear only when a second matching successful case promotes the candidate into a real saved routine, or later when an already saved routine is reused.
- Risk is HIGH because this slice touches the live response path that the user already reproduced as wrong in Janus runtime, and it spans promotion, orchestration, and user-facing routine messaging behavior across multiple backend surfaces.
Affected Files:
- backend/services/workflow/workflow_offer_service.py
- backend/services/workflow/routine_runner.py
- backend/services/chat_orchestrator.py
- backend/services/orchestrator/response_finalizer.py
- backend/tests/test_workflow_offer_service.py
- backend/tests/test_routine_runner.py
- backend/tests/unit/test_chat_orchestrator_routine_execution.py
- documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29.2_task_breakdown.md
- documentation/tasks/TASK-SPEC29.2_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Evidence Focus:
- python -m pytest backend/tests/test_workflow_offer_service.py -v
- python -m pytest backend/tests/test_routine_runner.py -v
- python -m pytest backend/tests/unit/test_chat_orchestrator_routine_execution.py -v
- python -m py_compile backend/services/workflow/workflow_offer_service.py backend/services/workflow/routine_runner.py backend/services/chat_orchestrator.py backend/services/orchestrator/response_finalizer.py
- git diff --check -- backend/services/workflow/workflow_offer_service.py backend/services/workflow/routine_runner.py backend/services/chat_orchestrator.py backend/services/orchestrator/response_finalizer.py backend/tests/test_workflow_offer_service.py backend/tests/test_routine_runner.py backend/tests/unit/test_chat_orchestrator_routine_execution.py documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md documentation/tasks/TASK-SPEC29.2_task_breakdown.md documentation/tasks/TASK-SPEC29.2_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not add settings management, routines API, visible routine lists, deletion/deactivation controls, or broader workflow-learning redesign in this slice.
- Preserve fail-closed behavior: failed, too-late, non-matching, risky, sensitive, or otherwise ineligible follow-up cases must not promote.
- Probe the shared execution gate again before code changes so Cursor visibility evidence stays current for this write-capable slice, but Codex remains owner of final review, validation, and state updates.
Automated Evidence Gate:
- python -m pytest backend/tests/test_workflow_offer_service.py -v
- python -m pytest backend/tests/test_routine_runner.py -v
- python -m pytest backend/tests/unit/test_chat_orchestrator_routine_execution.py -v
- python -m py_compile backend/services/workflow/workflow_offer_service.py backend/services/workflow/routine_runner.py backend/services/chat_orchestrator.py backend/services/orchestrator/response_finalizer.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- documentation/tasks/TASK-SPEC29.1_execution_result.md
- documentation/tasks/TASK-SPEC29.1_debug_result.md
- documentation/tasks/TASK-SPEC29.2_task_breakdown.md
- backend/services/workflow/workflow_offer_service.py
- backend/services/workflow/routine_runner.py
- backend/services/chat_orchestrator.py
- backend/services/orchestrator/response_finalizer.py
- backend/tests/test_workflow_offer_service.py
- backend/tests/test_routine_runner.py
- backend/tests/unit/test_chat_orchestrator_routine_execution.py
Drop Context:
- stale old-chain `TASK-SPEC29.2_*` worker-gateway history
- later TASK-SPEC29.3 settings management and routines API work
- unrelated workflow delegation rollout work and unrelated dirty worktree changes
- broader autonomous learning ideas outside the approved v1 routine scope
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: TASK-SPEC29.2 is now a bounded but user-visible runtime slice with explicit files, tests, and a concrete live failure to close.
User Action: Continue with janus-executioner for `TASK-SPEC29.2`, and probe the shared execution gate for a sensible Cursor-first write-capable lane before local implementation.
