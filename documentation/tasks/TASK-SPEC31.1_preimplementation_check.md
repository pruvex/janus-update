PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: TASK-SPEC31.1
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
Spec: documentation/SPEC/31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
Backlog Item: BACKLOG-123
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: extend the existing saved-routine execution path so a natural request from the pilot family `calendar.list_events + system.routing` can reuse a matching saved routine through a general semantic multi-step routine core.
- The slice must preserve the current passive routine-used hint behavior and keep the existing `calendar.list_events + system.weather` path working as a regression reference.
- Current user values must take precedence over historical routine-run values. This slice is about the reusable semantic core and first safe routing pilot only; the later hardening slice `TASK-SPEC31.2` remains separate.
- Risk is HIGH because this changes live saved-routine execution behavior across matching, runtime parameter binding, and user-visible answer flow on the existing backend path.
- Artifact identity is consistent across `BACKLOG-123`, the approved Spec 31, the generated `TASK-SPEC31` artifact, and the released breakdown handoff `TASK-SPEC31.1`.
Affected Files:
- backend/services/orchestrator/intent_engine.py
- backend/services/workflow/routine_runner.py
- backend/services/chat_orchestrator.py
- backend/tests/test_routine_runner.py
- backend/tests/test_workflow_offer_service.py
- backend/tests/unit/test_chat_orchestrator_routine_execution.py
- documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- documentation/tasks/TASK-SPEC31.1_task_breakdown.md
- documentation/tasks/TASK-SPEC31.1_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
Evidence Focus:
- python -m pytest backend/tests/test_routine_runner.py -v
- python -m pytest backend/tests/test_workflow_offer_service.py -v
- python -m pytest backend/tests/unit/test_chat_orchestrator_routine_execution.py -v
- python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/workflow/routine_runner.py backend/services/chat_orchestrator.py
- git diff --check -- backend/services/orchestrator/intent_engine.py backend/services/workflow/routine_runner.py backend/services/chat_orchestrator.py backend/tests/test_routine_runner.py backend/tests/test_workflow_offer_service.py backend/tests/unit/test_chat_orchestrator_routine_execution.py documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md documentation/tasks/TASK-SPEC31.1_task_breakdown.md documentation/tasks/TASK-SPEC31.1_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- Do not absorb `TASK-SPEC31.2` hardening work in this slice. No broad ambiguity framework, no future routine families, no routine-management UI, no embedding/vector search, and no unrelated workflow architecture changes.
- Probe the shared execution gate before code changes so the current Cursor-first write-capable lane visibility is captured for this bounded slice, but Codex remains owner of final review, validation, and state updates.
Automated Evidence Gate:
- python -m pytest backend/tests/test_routine_runner.py -v
- python -m pytest backend/tests/test_workflow_offer_service.py -v
- python -m pytest backend/tests/unit/test_chat_orchestrator_routine_execution.py -v
- python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/workflow/routine_runner.py backend/services/chat_orchestrator.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/SPEC/31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- documentation/tasks/TASK-SPEC31.1_task_breakdown.md
- documentation/tasks/TASK-SPEC31.1_preimplementation_check.md
- documentation/Planned Features/backlog_BACKLOG-123_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- backend/services/orchestrator/intent_engine.py
- backend/services/workflow/routine_runner.py
- backend/services/chat_orchestrator.py
- backend/tests/test_routine_runner.py
- backend/tests/test_workflow_offer_service.py
- backend/tests/unit/test_chat_orchestrator_routine_execution.py
Drop Context:
- later TASK-SPEC31.2 fail-closed hardening and ambiguity expansion work
- old Spec-29.2 debug chain except where it already informed the approved Spec 31 boundaries
- unrelated backlog items, country-info fallout, and unrelated dirty worktree changes
- broader future routine-family ideas outside the locked pilot boundary
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: TASK-SPEC31.1 is now a bounded but user-visible backend slice on the live saved-routine execution path with explicit files, tests, and a clear pilot boundary.
User Action: Continue with janus-executioner for `TASK-SPEC31.1`, and probe the shared execution gate for a sensible Cursor-first write-capable lane before local implementation.
