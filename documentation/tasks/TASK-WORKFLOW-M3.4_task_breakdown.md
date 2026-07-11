TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
- Task File: documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
- Target Task: TASK-WORKFLOW-M3.4
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Workflow Spec vision and section 2.4/7 Phase 4 plus the corrected M3.3 execution result. This slice is limited to semantic reuse of an already saved routine from a later natural user request. It must not widen into UI, transport, OAuth, product OpenRouter, delegation hardening, broader Memory Session-Search, or autonomous routine execution without a user request.
- Files: backend/services/workflow/routine_runner.py, backend/services/orchestrator/intent_engine.py, backend/services/chat_orchestrator.py, backend/tests/test_routine_runner.py, backend/tests/test_workflow_offer_service.py
- Tests: run `python -m pytest backend/tests/test_routine_runner.py backend/tests/test_workflow_offer_service.py -v`; run `python -m py_compile backend/services/workflow/routine_runner.py backend/services/orchestrator/intent_engine.py backend/services/chat_orchestrator.py`; run scoped `git diff --check`
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. The acceptance target is not a generated routine-name trigger; the saved calendar-plus-weather routine must be found from a semantically matching natural user request and the response must say that a saved routine was used.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
Task: documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
Backlog Item: N/A
Target Task: TASK-WORKFLOW-M3.4
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
