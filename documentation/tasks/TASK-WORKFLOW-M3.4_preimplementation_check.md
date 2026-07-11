PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: TASK-WORKFLOW-M3.4
Target Subtask: N/A
Task: documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: extend the existing backend routine runner so a saved routine can be reused from a later semantically matching natural user request, without requiring the generated routine name or magic phrase.
- The primary acceptance case is a saved calendar-plus-weather routine from `Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?`; repeating the same or equivalent natural request must execute the saved routine and say the routine was used.
- Explicit trigger phrase execution must continue to work, and unrelated natural requests must not execute a routine.
- Risk is MEDIUM because this changes live routine execution matching, but the scope remains backend-only and bounded to a user-initiated request.
Affected Files:
- backend/services/workflow/routine_runner.py
- backend/services/orchestrator/intent_engine.py
- backend/services/chat_orchestrator.py
- backend/tests/test_routine_runner.py
- backend/tests/test_workflow_offer_service.py
- documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
- documentation/tasks/TASK-WORKFLOW-M3.4_task_breakdown.md
- documentation/tasks/TASK-WORKFLOW-M3.4_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Evidence Focus:
- python -m pytest backend/tests/test_routine_runner.py backend/tests/test_workflow_offer_service.py -v
- python -m pytest backend/tests/test_workflow_detector.py backend/tests/test_workflow_offer_service.py backend/tests/test_routine_runner.py backend/tests/test_routine_placeholder_resolver.py backend/tests/test_execution_dispatcher_weather_guard.py backend/tests/test_agent_factory_runtime.py backend/tests/unit/test_response_finalizer_calendar_weather_combo.py -q
- python -m py_compile backend/services/workflow/routine_runner.py backend/services/orchestrator/intent_engine.py backend/services/chat_orchestrator.py
- git diff --check -- backend/services/workflow/routine_runner.py backend/services/orchestrator/intent_engine.py backend/services/chat_orchestrator.py backend/tests/test_routine_runner.py backend/tests/test_workflow_offer_service.py documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md documentation/tasks/TASK-WORKFLOW-M3.4_task_breakdown.md documentation/tasks/TASK-WORKFLOW-M3.4_preimplementation_check.md documentation/tasks/TASK-WORKFLOW-M3.4_execution_result.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not add UI, transport APIs, OAuth, product OpenRouter, Memory Session-Search, broad semantic embeddings, or autonomous routine execution without a user request.
- Cursor Composer must be offered/used first for the bounded write-capable slice when the shared delegation gate exposes it; Codex remains owner of review, validation, and final state.
Automated Evidence Gate:
- python -m pytest backend/tests/test_routine_runner.py backend/tests/test_workflow_offer_service.py -v
- python -m pytest backend/tests/test_workflow_detector.py backend/tests/test_workflow_offer_service.py backend/tests/test_routine_runner.py backend/tests/test_routine_placeholder_resolver.py backend/tests/test_execution_dispatcher_weather_guard.py backend/tests/test_agent_factory_runtime.py backend/tests/unit/test_response_finalizer_calendar_weather_combo.py -q
- python -m py_compile backend/services/workflow/routine_runner.py backend/services/orchestrator/intent_engine.py backend/services/chat_orchestrator.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
- documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
- documentation/tasks/TASK-WORKFLOW-M3.4_task_breakdown.md
- documentation/tasks/TASK-WORKFLOW-M3.4_preimplementation_check.md
- backend/services/workflow/routine_runner.py
- backend/services/orchestrator/intent_engine.py
- backend/services/chat_orchestrator.py
- backend/tests/test_routine_runner.py
- backend/tests/test_workflow_offer_service.py
Drop Context:
- old M3.3 weather-only/debug failures except as regression tests already captured
- Workflow Phase 5 UI details
- transport, OAuth, OpenRouter product routing, delegation hardening, and Memory Session-Search work
- unrelated dirty worktree changes
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The semantic routine-reuse correction is now precheck-ready as one bounded backend implementation block with Cursor-first workhorse evidence.
User Action: Continue with Cursor Composer first for `TASK-WORKFLOW-M3.4`.
