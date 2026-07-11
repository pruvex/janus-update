TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
- Task File: documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
- Target Task: TASK-WORKFLOW-M3.3
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Workflow Spec section 7 Phase 4 plus Roadmap section 4 M3. This slice is limited to routine trigger matching, placeholder resolution for bounded user context, sequential routine step execution, and persistence of run metadata. It must not widen into UI, transport, OAuth, product OpenRouter, delegation hardening, or broader memory/session-search work.
- Files: backend/services/workflow/routine_runner.py, backend/services/workflow/placeholder_resolver.py, backend/services/orchestrator/intent_engine.py, backend/services/chat_orchestrator.py, backend/tests/test_routine_runner.py, backend/tests/test_routine_placeholder_resolver.py, minimal routine-store touchpoints only if required for run metadata persistence
- Tests: run `python -m pytest backend/tests/test_routine_runner.py -v`; run `python -m pytest backend/tests/test_routine_placeholder_resolver.py -v`; run `python -m py_compile backend/services/workflow/routine_runner.py backend/services/workflow/placeholder_resolver.py backend/services/orchestrator/intent_engine.py backend/services/chat_orchestrator.py`; run scoped `git diff --check`
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. This slice is product-relevant because it executes persisted routine steps and resolves bounded placeholders from user context, but it remains bounded to the Workflow Phase 4 backend path only.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
Task: documentation/tasks/TASK-WORKFLOW-M3_offer_runner.md
Backlog Item: N/A
Target Task: TASK-WORKFLOW-M3.3
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
