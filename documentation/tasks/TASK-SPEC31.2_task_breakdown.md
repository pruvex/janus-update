TASK BREAKDOWN RESULT
- Spec: documentation/SPEC/31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- Task File: documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
- Target Task: TASK-SPEC31.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: approved Spec 31 plus generated TASK-SPEC31 artifact. This second Spec-31 slice is limited to fail-closed guards, ambiguity boundaries, and negative regression hardening for the already-delivered general semantic routine-reuse core. It may harden the existing `calendar.list_events + system.routing` pilot and the preserved `calendar.list_events + system.weather` path, but it must not reopen the already accepted positive pilot behavior, widen into new routine families, add UI, add embedding/vector search, or introduce broader workflow/product redesign.
- Files: backend/services/orchestrator/intent_engine.py, backend/services/workflow/routine_runner.py, backend/tests/test_routine_runner.py, backend/tests/test_workflow_offer_service.py
- Acceptance Criteria: when required parameters are missing or cannot be extracted safely, Janus does not reuse an old saved routine with stale values; when a new request contains explicit conflicting or changed values, those values are not silently overwritten by historical routine-run values; when multiple saved routines only partially or superficially match, Janus stays on the normal request path instead of aggressively false-matching; regression coverage protects both the routing pilot and the existing weather reuse family.
- Tests: run `python -m pytest backend/tests/test_routine_runner.py -v`; run `python -m pytest backend/tests/test_workflow_offer_service.py -v`; run `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/workflow/routine_runner.py`; run scoped `git diff --check`.
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. `TASK-SPEC31.1` is already sealed, so this slice only hardens the same productive reuse path against parameter gaps, conflicts, and ambiguity without changing the accepted positive routing pilot surface or broadening the feature boundary.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, high

```text
@janus-preimplementation-check
Spec: documentation/SPEC/31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
Task: documentation/tasks/TASK-SPEC31_semantisches_parameterisiertes_routine_reuse_mehrschrittige_routinen.md
Backlog Item: BACKLOG-123
Target Task: TASK-SPEC31.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
