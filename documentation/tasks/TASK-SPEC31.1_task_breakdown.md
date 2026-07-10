TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- Task File: documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- Target Task: TASK-SPEC31.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Approved Spec 31 plus generated TASK-SPEC31 artifact. This slice is limited to the general semantic reuse core on the existing saved-routine path, the first bounded pilot for `calendar.list_events + system.routing`, fresh parameter rebinding with current user values taking precedence, and preservation of the existing `calendar.list_events + system.weather` path as a regression reference. It must not widen into ambiguity hardening beyond clearly necessary pilot-safe guards, future routine families, routine-management UI, embedding/vector search, or broader product architecture changes.
- Files: backend/services/orchestrator/intent_engine.py, backend/services/workflow/routine_runner.py, backend/services/chat_orchestrator.py, backend/tests/test_routine_runner.py, backend/tests/test_workflow_offer_service.py, backend/tests/unit/test_chat_orchestrator_routine_execution.py
- Acceptance Criteria: a natural request from the pilot family `calendar.list_events + system.routing` can reuse a matching saved routine with current request values; current request values for date, start, or destination take precedence over historical routine-run values; the existing natural reuse path for `calendar.list_events + system.weather` remains intact; successful reuse still shows only a short passive routine-used hint.
- Tests: run `python -m pytest backend/tests/test_routine_runner.py -v`; run `python -m pytest backend/tests/test_workflow_offer_service.py -v`; run `python -m pytest backend/tests/unit/test_chat_orchestrator_routine_execution.py -v`; run `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/workflow/routine_runner.py backend/services/chat_orchestrator.py`; run scoped `git diff --check`
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. This slice only establishes the reusable semantic multi-step routine core plus the first safe routing pilot on the existing backend path; the later hardening slice `TASK-SPEC31.2` remains separate so implementation does not silently absorb all ambiguity and fail-closed edge cases at once.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

```text
@janus-preimplementation-check
Spec: documentation/SPEC/31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
Task: documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
Backlog Item: BACKLOG-123
Target Task: TASK-SPEC31.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
