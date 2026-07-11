TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
- Task File: documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
- Target Task: TASK-SPEC29.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 29 plus generated TASK-SPEC29 artifact. This slice is limited to second-hit promotion and the user-visible transition from the old explicit save-offer flow to passive transparency for the in-scope silent-learning path. It must not widen into settings management, routines API, broader UI redesign, unrelated workflow architecture, or the later visible routine-management surface.
- Files: backend/services/workflow/workflow_offer_service.py, backend/services/workflow/routine_runner.py, backend/services/chat_orchestrator.py, backend/services/orchestrator/response_finalizer.py, backend/tests/test_workflow_offer_service.py, backend/tests/test_routine_runner.py, backend/tests/unit/test_chat_orchestrator_routine_execution.py
- Acceptance Criteria: a first qualifying successful multi-step workflow no longer emits the old explicit save prompt or `JANUS_ROUTINE_OFFER` marker for this in-scope silent-learning path; a second matching successful case within 30 days promotes the hidden candidate to a real saved routine; passive chat messaging appears only at promotion time or later routine reuse; failed, too-late, or non-matching follow-up cases do not promote; already-saved routine reuse still produces only a short passive hint.
- Tests: run `python -m pytest backend/tests/test_workflow_offer_service.py -v`; run `python -m pytest backend/tests/test_routine_runner.py -v`; run `python -m pytest backend/tests/unit/test_chat_orchestrator_routine_execution.py -v`; run `python -m py_compile backend/services/workflow/workflow_offer_service.py backend/services/workflow/routine_runner.py backend/services/chat_orchestrator.py backend/services/orchestrator/response_finalizer.py`; run scoped `git diff --check`
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. The live failure from `TASK-SPEC29.1` proved that the old offer/save path still fires in runtime, so this slice now has a concrete bounded target: suppress the legacy prompt for the silent-learning path while preserving promotion, reuse signaling, and fail-closed matching boundaries.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

```text
@janus-preimplementation-check
Spec: documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md
Task: documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md
Backlog Item: N/A
Target Task: TASK-SPEC29.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
