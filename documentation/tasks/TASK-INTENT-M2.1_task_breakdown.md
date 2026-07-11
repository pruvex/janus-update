TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
- Task File: documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md
- Target Task: TASK-INTENT-M2.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Intent Spec section 6 plus Roadmap section 4 M2. This slice is limited to confidence-based routing and ambiguity softening on top of the sealed M1 auxiliary-classifier baseline. It must not widen into Regex-Freeze implementation (`TASK-INTENT-M2.2`), Entity-First routing, Memory follow-up phases, Transport, OAuth, OpenRouter, or delegation hardening.
- Files: backend/services/orchestrator/execution_dispatcher.py, backend/services/orchestrator/intent_engine.py, backend/tests/test_intent_confidence_routing.py, backend/tests/test_calendar_routing_fix.py, backend/tests/test_intent_benchmark.py, directly affected existing intent or routing regressions only if needed to preserve current guardrails
- Acceptance Criteria: Ambiguity False Positives improve measurably within the M2 target band (`-30%` to `-50%`) or the blocker is documented clearly; high or sufficient confidence Contact/Pet/Recall paths are no longer unnecessarily blocked by `disable_tools=True`; backend/tests/test_calendar_routing_fix.py stays fully green; Safety-, Medical-, Consent-, and Personal-Recall-Web-Guard behavior remains unchanged.
- Tests: run `python -m pytest backend/tests/test_intent_confidence_routing.py -q`; run `python -m pytest backend/tests/test_calendar_routing_fix.py backend/tests/test_intent_benchmark.py -q`; run `python -m py_compile backend/services/orchestrator/execution_dispatcher.py backend/services/orchestrator/intent_engine.py`; run `python -m backend.scripts.run_intent_benchmark --mode m2-proof --output documentation/test-runs/TASK-INTENT-M2.1_confidence_routing_2026-07-08.md`; run scoped `git diff --check` on the touched intent, benchmark, and task-chain artifacts
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. The M1 classifier and Memory MA/MB slice are already sealed, so this M2 step may only soften the ambiguity hard-block, preserve all existing safety boundaries, and prove the routing uplift against the established benchmark path. It must not silently absorb the optional Regex-Freeze follow-up or broader routing redesign.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md
Task: documentation/tasks/TASK-INTENT-M2_confidence_routing_and_regex_freeze.md
Backlog Item: N/A
Target Task: TASK-INTENT-M2.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
