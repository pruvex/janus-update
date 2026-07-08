TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- Task File: documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
- Target Task: TASK-MEM-M1.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Memory Spec sections 4 and 5 plus Roadmap section 4 M1. This slice is limited to Phase A Hot-Layer-Caps and Phase B On-Demand Memory Injection. It must not widen into Session-Search (Phase C), Frozen Core (Phase D), USER.md export (Phase E), Intent M2 confidence routing, Transport, OAuth, OpenRouter, or delegation hardening.
- Files: backend/services/memory/retrieval_service.py, backend/services/memory_budget.py, backend/services/memory_observability.py, backend/services/chat_orchestrator.py, backend/services/orchestrator/intent_engine.py only if a minimal existing signal reuse is required, backend/tests/test_memory_hot_layer_cap.py, backend/tests/test_memory_on_demand_injection.py, directly affected existing memory regression tests
- Tests: run `python -m pytest backend/tests/test_memory_hot_layer_cap.py -v`; run `python -m pytest backend/tests/test_memory_on_demand_injection.py -v`; run `python -m pytest backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py -q`; run `python -m py_compile backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py`; run scoped `git diff --check` on the touched memory/task artifacts
- Execution Model: 5.4
- Readiness: Scope is atomic and precheck-ready. The slice is small enough for one bounded implementation block, but still product-relevant enough that Health/Medical protection, flag-off parity, and weather-vs-personal gating must remain explicit acceptance boundaries.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.4, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
Task: documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
Backlog Item: N/A
Target Task: TASK-MEM-M1.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.4
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```

