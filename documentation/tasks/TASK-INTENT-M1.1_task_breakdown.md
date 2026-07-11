TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- Task File: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
- Target Task: TASK-INTENT-M1.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Intent Spec section 5 plus the compiled TASK-INTENT-M1 artifact. This first M1 slice is only the auxiliary classifier contract, provider wrapper, config flag surface, and focused unit coverage. It must not widen into `detect_all_intents()` integration, benchmark uplift proof, staging enablement, Memory A/B work, or any transport/provider-product refactor.
- Files: backend/services/orchestrator/intent_aux_classifier.py, backend/services/orchestrator/intent_config.py, backend/data/schemas_intent.py, backend/tests/test_intent_aux_classifier.py, backend/tests/test_intent_action_subject_mapping.py
- Acceptance Criteria: the auxiliary classifier returns only validated `ActionSubjectResult` objects or a deterministic fallback outcome; config flag `off` does not change the effective external routing behavior; provider, JSON, or parsing failures fail closed and do not create a new uncontrolled route; the contract surface is locally testable without live provider calls.
- Tests: run `python -m pytest backend/tests/test_intent_aux_classifier.py -q`; run `python -m pytest backend/tests/test_intent_action_subject_mapping.py -q`; run `python -m py_compile backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py backend/data/schemas_intent.py`; run `git diff --check` on the touched service, schema, test, and task-chain artifacts.
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. This slice may define the new classifier contract and its bounded fallback/config behavior, but it must not yet wire the classifier into `detect_all_intents()` or claim any benchmark uplift. Existing intent-engine behavior should remain externally unchanged when the feature flag is off.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Task: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Backlog Item: N/A
Target Task: TASK-INTENT-M1.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
