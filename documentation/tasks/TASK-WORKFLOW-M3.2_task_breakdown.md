TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
- Task File: documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
- Target Task: TASK-WORKFLOW-M3.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Workflow Spec section 7 Phase 3 plus Roadmap section 4 M3. This slice is limited to proactive routine offers, explicit save/decline dialog handling, and bounded persistence for offer outcomes. It must not widen into routine execution (Phase 4), routines UI (Phase 5), Memory Session-Search, Transport, OAuth, OpenRouter product routing, or delegation hardening.
- Files: backend/services/workflow/workflow_offer_service.py, backend/services/orchestrator/intent_engine.py, backend/services/orchestrator/response_finalizer.py, backend/tests/test_workflow_offer_service.py, backend/tests/test_routine_intent_patterns.py, minimal workflow persistence touchpoints only if required for offer outcome storage
- Tests: run `python -m pytest backend/tests/test_workflow_offer_service.py -v`; run `python -m pytest backend/tests/test_routine_intent_patterns.py -v`; run `python -m py_compile backend/services/workflow/workflow_offer_service.py backend/services/orchestrator/intent_engine.py backend/services/orchestrator/response_finalizer.py`; run scoped `git diff --check`
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. This slice is product-relevant because it changes conversational output and persists explicit offer/save outcomes, but it remains bounded before any runner execution path.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
Task: documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
Backlog Item: N/A
Target Task: TASK-WORKFLOW-M3.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
