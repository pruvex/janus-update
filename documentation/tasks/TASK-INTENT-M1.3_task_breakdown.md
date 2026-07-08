TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- Task File: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
- Target Task: TASK-INTENT-M1.3
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Intent Spec sections 5.6, 5.8, and 5.9 plus the compiled TASK-INTENT-M1 artifact and the checked-in M0 baseline in documentation/test-runs/INTENT_BENCHMARK_BASELINE.md. This third M1 slice is evidence-only closure for the auxiliary classifier: benchmark uplift versus M0, latency guardrails, flag-off parity proof, and staged-enablement readiness. It must not widen into new intent features, M2 confidence-routing, Memory A/B, transport, OAuth, or delegation hardening.
- Files: backend/scripts/run_intent_benchmark.py, backend/tests/test_intent_benchmark.py, backend/tests/test_intent_aux_classifier.py, backend/tests/test_calendar_routing_fix.py, documentation/test-runs/INTENT_BENCHMARK_BASELINE.md, documentation/test-runs/
- Acceptance Criteria: Contact/Pet/Recall show at least +12 pp against the M0 baseline or the blocker is documented clearly; backend/tests/test_calendar_routing_fix.py stays green; P95 latency of the auxiliary classifier stays below 400 ms or a credible blocker is documented; flag off remains identical to legacy behavior.
- Tests: run `python -m pytest backend/tests/test_intent_benchmark.py backend/tests/test_intent_aux_classifier.py backend/tests/test_calendar_routing_fix.py -q`; run `python -m backend.scripts.run_intent_benchmark --write-baseline`; capture a targeted latency or telemetry check for the auxiliary classifier execution path; run scoped `git diff --check` on the touched benchmark, test, and task-chain artifacts.
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. M1.1 and M1.2 are already sealed, so this slice may only rerun the benchmark against the M0 baseline, prove latency and flag-off guardrails, and prepare the evidence package for final audit and staged enablement. It must not reopen integration logic or claim exit PASS without the measured uplift and latency evidence.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Task: documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
Backlog Item: N/A
Target Task: TASK-INTENT-M1.3
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
