TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
- Task File: documentation/tasks/TASK-WORKFLOW-M3_learned_workflows_phase_1_2.md
- Target Task: TASK-WORKFLOW-M3.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Workflow Spec section 7 Phase 1+2 plus Roadmap section 4 M3. This slice is limited to Routine-Store, Schema, Detector, and Step-Trace extraction. It must not widen into proactive offer flow (Phase 3), routine execution (Phase 4), routines UI (Phase 5), Memory Session-Search, Transport, OAuth, OpenRouter product routing, or delegation hardening.
- Files: backend/data/models.py, backend/data/database.py, backend/services/workflow/routine_store.py, backend/services/workflow/routine_schema.py, backend/services/workflow/workflow_detector.py, backend/services/workflow/step_trace_extractor.py, backend/services/capability_registry.py only if minimal validation wiring is required, backend/tests/test_routine_store.py, backend/tests/test_workflow_detector.py, directly affected existing workflow/orchestrator regression tests if needed for real KPI-trace fixtures
- Tests: run `python -m pytest backend/tests/test_routine_store.py -v`; run `python -m pytest backend/tests/test_workflow_detector.py -v`; run `python -m py_compile backend/services/workflow/routine_store.py backend/services/workflow/routine_schema.py backend/services/workflow/workflow_detector.py backend/services/workflow/step_trace_extractor.py`; run scoped `git diff --check` on the touched workflow/task artifacts
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. The slice is product-relevant because it introduces persisted routine metadata and interprets workflow traces, but it stays bounded by `ROUTINES_ENABLED=false`, no offer text, and no runner execution path.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md
Task: documentation/tasks/TASK-WORKFLOW-M3_learned_workflows_phase_1_2.md
Backlog Item: N/A
Target Task: TASK-WORKFLOW-M3.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
