TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- Task File: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
- Target Task: TASK-INTENT-M1.2
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Intent Spec section 5.6 plus the compiled TASK-INTENT-M1 artifact. This second M1 slice is only the `detect_all_intents()` integration for the already-delivered auxiliary classifier, including merge rules, safety-veto preservation, circuit-breaker fallback, and bounded regressions. It must not widen into M1.3 benchmark uplift proof, staging enablement, Memory A/B work, transport, OAuth, or product OpenRouter changes.
- Files: backend/services/orchestrator/intent_engine.py, backend/services/orchestrator/intent_aux_classifier.py, backend/services/orchestrator/intent_config.py, backend/tests/test_calendar_routing_fix.py, backend/tests/test_intent_aux_classifier.py, backend/tests/test_intent_action_subject_mapping.py
- Acceptance Criteria: `INTENT_AUX_CLASSIFIER_ENABLED=false` preserves the effective legacy routing path; enabled auxiliary classification merges according to the spec confidence bands (`>=0.80`, `0.55-0.79`, `<0.55`) without bypassing the safety veto; repeated auxiliary failures fail closed into the deterministic fallback path; Contact/Pet/Recall and existing Calendar/Shopping/Weather/Routing flows gain regression coverage without introducing uncontrolled new routes.
- Tests: run `python -m pytest backend/tests/test_intent_aux_classifier.py backend/tests/test_intent_action_subject_mapping.py -q`; run `python -m pytest backend/tests/test_calendar_routing_fix.py -q`; run `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/orchestrator/intent_aux_classifier.py backend/services/orchestrator/intent_config.py`; run `git diff --check` on the touched orchestrator, test, and task-chain artifacts.
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. M1.1 is already sealed, so this slice may wire the classifier into `detect_all_intents()` and add the merge/fallback behavior from spec section 5.6, but it must not claim benchmark uplift, flip staging flags, or expand into the M1.3 proof surface.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Task: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Backlog Item: N/A
Target Task: TASK-INTENT-M1.2
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
