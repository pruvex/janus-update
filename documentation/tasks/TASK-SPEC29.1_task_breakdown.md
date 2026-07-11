TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
- Task File: documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- Target Task: TASK-SPEC29.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Approved Spec 29 plus generated TASK-SPEC29 artifact. This slice is limited to the hidden candidate lifecycle, 30-day expiry, and fail-closed learning guards for v1. It must not widen into automatic promotion, passive chat transparency, settings management, routine management UI, new transport paths, OAuth, or broader autonomous learning behavior.
- Files: backend/data/models.py, backend/data/database.py, backend/services/workflow/workflow_detector.py, backend/services/workflow/step_trace_extractor.py, backend/services/workflow/routine_store.py, backend/tests/test_workflow_detector.py, backend/tests/test_routine_store.py
- Tests: run `python -m pytest backend/tests/test_workflow_detector.py -v`; run `python -m pytest backend/tests/test_routine_store.py -v`; run `python -m py_compile backend/data/models.py backend/data/database.py backend/services/workflow/workflow_detector.py backend/services/workflow/step_trace_extractor.py backend/services/workflow/routine_store.py`; run scoped `git diff --check`
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. The slice only establishes internal candidate persistence, suitability guards, and 30-day expiry; it does not yet create visible saved routines or user-facing settings controls.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
Task: documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
Backlog Item: N/A
Target Task: TASK-SPEC29.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
