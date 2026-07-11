PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-WORKFLOW-M3.3
Target Subtask: N/A
Task: documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: implement Workflow Phase 4 routine execution as one guarded slice with trigger phrase matching, placeholder resolution for bounded user context, sequential step execution, policy-stop handling, and local run metadata persistence.
- Artifact identity is consistent across the Workflow spec section 7 Phase 4, the roadmap M3 entry, the compiled task artifact `documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md`, and the released handoff `documentation/tasks/TASK-WORKFLOW-M3.3_task_breakdown.md`.
- The affected file cluster is concrete and intentionally bounded to workflow execution services, routine trigger helpers, and focused workflow regression tests.
- Risk is MEDIUM because this slice executes persisted routines and touches user-visible automation behavior, but it remains bounded before UI, transport, or provider-surface expansion.
Affected Files:
- backend/services/workflow/routine_runner.py
- backend/services/workflow/placeholder_resolver.py
- backend/services/orchestrator/intent_engine.py
- backend/services/chat_orchestrator.py
- backend/tests/test_routine_runner.py
- backend/tests/test_routine_placeholder_resolver.py
Evidence Focus:
- python -m pytest backend/tests/test_routine_runner.py -v
- python -m pytest backend/tests/test_routine_placeholder_resolver.py -v
- python -m py_compile backend/services/workflow/routine_runner.py backend/services/workflow/placeholder_resolver.py backend/services/orchestrator/intent_engine.py backend/services/chat_orchestrator.py
- git diff --check -- backend/services/workflow/routine_runner.py backend/services/workflow/placeholder_resolver.py backend/services/orchestrator/intent_engine.py backend/services/chat_orchestrator.py backend/tests/test_routine_runner.py backend/tests/test_routine_placeholder_resolver.py documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md documentation/tasks/TASK-WORKFLOW-M3.3_task_breakdown.md documentation/tasks/TASK-WORKFLOW-M3.3_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_routine_runner.py -v
- python -m pytest backend/tests/test_routine_placeholder_resolver.py -v
- python -m py_compile backend/services/workflow/routine_runner.py backend/services/workflow/placeholder_resolver.py backend/services/orchestrator/intent_engine.py backend/services/chat_orchestrator.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
- documentation/tasks/TASK-WORKFLOW-M3.3_task_breakdown.md
- backend/services/workflow/routine_schema.py
- backend/services/workflow/routine_store.py
- backend/services/workflow/workflow_offer_service.py
- backend/services/workflow/workflow_detector.py
Drop Context:
- sealed Workflow M3.1 and M3.2 details except for store, detector, and offer APIs the runner consumes
- Workflow Phase 5 UI details
- Transport, OAuth, OpenRouter product routing, and delegation hardening work
- unrelated dirty worktree changes
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The M3.3 routine-runner slice is now precheck-ready as one bounded execution block with trigger matching, placeholder resolution, and local validation gates.
User Action: Say `ok` to continue with local implementation and validation for `TASK-WORKFLOW-M3.3`.
